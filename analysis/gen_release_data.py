# -*- coding: utf-8 -*-
"""Generator zawartosci release_data/ - macierze per-task, trajektorie, logi, podsumowania.

CO ROBI:
Buduje katalog release_data/ z siedmiu CZYSTYCH katalogow wynikowych (те na commitach
zgodnych z HEAD co do tasks/adversarial i src/polagentbench/eval). Cztery katalogi
zaminowane sa pomijane z nazwy - nie sa zrodlem niczego w paperze.

Produkuje piec plikow CSV:
  runs.csv               jeden wiersz na przebieg (37 przebiegow), z werdyktem zrodla
  per_task_main67.csv    dlugi format, suite main67 (67 zadan x komorka)
  per_task_ladder46.csv  dlugi format, suite ladder46 (46 zadan x komorka)
  per_task_variance.csv  sonda T=0.7, trzy ziarna, dwa kwanty
  matrix_main67_wide.csv widok szeroki: wiersz = zadanie, kolumna = komorka

WERDYKTY: wylacznie oracle. Tam gdzie katalog ma run.log - parsowany run.log.
Tam gdzie go nie ma - odtworzenie przez polagentbench.eval.smoke.evaluate.
Pole trajectory.success NIE jest werdyktem (zawyza w kazdej komorce; u PLLuM Q8 daje
66/67 wobec oracle 13/67) i trafia do CSV jako osobna kolumna, zeby czytelnik mogl
to sprawdzic samodzielnie.

KAZDA komorka jest walidowana: liczba zdanych musi rownac sie num_passed z summary.json.
Rozjazd przerywa generacje.

Uruchamiac z katalogu glownego repo:
  .venv/Scripts/python.exe analysis/gen_release_data.py
"""
from __future__ import annotations

import csv
import json
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from polagentbench.eval.smoke import SmokeStatus, evaluate  # noqa: E402
from polagentbench.io import load_all_tasks  # noqa: E402
from polagentbench.types import Trajectory  # noqa: E402

PASS_MARK = "✓"
FAIL_MARK = "✗"
LOGLINE = re.compile(r"^(\S+)\s+([" + PASS_MARK + FAIL_MARK + r"?])\s*(.*)$")

DST = Path("release_data")

# Siedem katalogow CZYSTYCH. Zaminowane (v3_full_2026-06-02, v3_ladder_2026-06-11,
# v3_run_2026-06-01, v3_run_2026-06-02_22task) swiadomie pominiete.
CLEAN = [
    "v3_arith_clean_2026-06-18",
    "v3_11b_2026-06-18",
    "v3_7b_grid_2026-07-29",
    "v3_pllum_2026-07-29",
    "v3_11b_ladder_2026-07-29",
    "v3_7b_ladder_2026-07-29",
    "v3_11b_variance_2026-07-29",
]

MAIN_TASKS = {t.id: t for t in load_all_tasks(Path("tasks/adversarial"))}
LADDER_TASKS = {t.id: t for t in load_all_tasks(Path("tasks/ladder_ext"))}
assert len(MAIN_TASKS) == 67 and len(LADDER_TASKS) == 46


def tier(task_id: str) -> str:
    return "easy" if task_id.startswith("adv_") else "hard"


def rung(task_id: str):
    m = re.match(r"^v3_ext_(L3N|L3T|L0|L1|L2)_([a-j])$", task_id)
    return (m.group(1), m.group(2)) if m else (None, None)


def read_runlog(run_dir: Path):
    """task_id -> (passed, tags) z run.log, albo None gdy pliku nie ma."""
    log = run_dir / "run.log"
    if not log.exists():
        return None
    out = {}
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
        m = LOGLINE.match(line)
        if not m:
            continue
        tail = m.group(3)
        tags = set()
        if " - " in tail:
            tags = {t.strip() for t in tail.rsplit(" - ", 1)[1].split(",") if t.strip()}
        out[m.group(1)] = (m.group(2) == PASS_MARK, tags)
    return out or None


def load_run(run_dir: Path):
    """Zwraca (summary, rows, verdict_source). rows: task_id -> dict."""
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    tasks = LADDER_TASKS if summary.get("num_tasks") == 46 else MAIN_TASKS
    log = read_runlog(run_dir)
    src = "run.log" if log else "eval.smoke.evaluate"

    rows = {}
    for line in (run_dir / "trajectories.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        tid = rec["task_id"]
        if log and tid in log:
            passed, tags = log[tid]
        else:
            res = evaluate(tasks[tid], Trajectory.model_validate(rec))
            passed = res.status is SmokeStatus.PASS
            tags = set(res.failure_tags)
        rows[tid] = {
            "task_id": tid,
            "passed": int(passed),
            "failure_tags": ";".join(sorted(tags)),
            "steps": len(rec.get("steps") or []),
            "total_tokens": rec.get("total_tokens"),
            "trajectory_success": int(bool(rec.get("success"))),
            "interface_variant": rec.get("interface_variant", ""),
            "seed": rec.get("seed"),
            "temperature": rec.get("temperature"),
        }

    got = sum(r["passed"] for r in rows.values())
    exp = summary["num_passed"]
    if got != exp or len(rows) != summary["num_tasks"]:
        raise SystemExit(
            f"ROZJAZD w {run_dir}: zdanych {got} vs summary {exp}, "
            f"zadan {len(rows)} vs {summary['num_tasks']}"
        )
    return summary, rows, src


def main() -> None:
    if DST.exists():
        shutil.rmtree(DST)
    for sub in ("matrices", "trajectories", "run_logs", "summaries"):
        (DST / sub).mkdir(parents=True, exist_ok=True)

    runs, main_rows, ladder_rows, var_rows = [], [], [], []
    n_log = n_reeval = 0

    for cat in CLEAN:
        base = Path("results") / cat
        for run_dir in sorted(p for p in base.iterdir() if p.is_dir()):
            if not (run_dir / "summary.json").exists():
                continue
            summary, rows, src = load_run(run_dir)
            n_log += src == "run.log"
            n_reeval += src != "run.log"

            slug = f"{cat}__{run_dir.name}"
            shutil.copy(run_dir / "trajectories.jsonl", DST / "trajectories" / f"{slug}.jsonl")
            shutil.copy(run_dir / "summary.json", DST / "summaries" / f"{slug}.json")
            if (run_dir / "run.log").exists():
                shutil.copy(run_dir / "run.log", DST / "run_logs" / f"{slug}.log")

            n = summary["num_tasks"]
            suite = "ladder46" if n == 46 else ("main67" if n == 67 else f"subset{n}")
            repair = "on" if "repair" in run_dir.name and "no_repair" not in run_dir.name else "off"
            is_var = cat == "v3_11b_variance_2026-07-29"
            cell = {
                "run_id": slug,
                "model_id": summary.get("model_id"),
                "quant": summary.get("quant"),
                "suite": suite,
                "repair": repair,
                "git_ref": summary.get("git_ref"),
                "verdict_source": src,
            }
            runs.append({
                **cell,
                "num_tasks": n,
                "num_passed": summary["num_passed"],
                "pass_rate": round(summary["num_passed"] / n, 4),
                "source_dir": str(run_dir).replace("\\", "/"),
            })

            target = var_rows if is_var else (ladder_rows if suite == "ladder46" else main_rows)
            for tid in sorted(rows):
                r = rows[tid]
                rec = {**cell, **r}
                if suite == "ladder46":
                    rec["rung"], rec["instance"] = rung(tid)
                else:
                    rec["tier"] = tier(tid)
                target.append(rec)

    def dump(name, data):
        if not data:
            return 0
        keys = list(data[0].keys())
        for d in data:
            for k in d:
                if k not in keys:
                    keys.append(k)
        with (DST / "matrices" / name).open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            w.writerows(data)
        return len(data)

    counts = {
        "runs.csv": dump("runs.csv", runs),
        "per_task_main67.csv": dump("per_task_main67.csv", main_rows),
        "per_task_ladder46.csv": dump("per_task_ladder46.csv", ladder_rows),
        "per_task_variance.csv": dump("per_task_variance.csv", var_rows),
    }

    # widok szeroki: wiersz = zadanie main67, kolumna = komorka model/kwant/repair
    wide_cells, wide = [], {}
    for r in main_rows:
        col = f"{r['model_id']}|{r['quant']}|{r['repair']}"
        if col not in wide_cells:
            wide_cells.append(col)
        wide.setdefault(r["task_id"], {"task_id": r["task_id"], "tier": r["tier"]})[col] = r["passed"]
    with (DST / "matrices" / "matrix_main67_wide.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["task_id", "tier"] + wide_cells)
        w.writeheader()
        w.writerows([wide[k] for k in sorted(wide)])
    counts["matrix_main67_wide.csv"] = len(wide)

    total = sum(f.stat().st_size for f in DST.rglob("*") if f.is_file())
    print("=== release_data/ ZBUDOWANE ===")
    for k, v in counts.items():
        print(f"  matrices/{k:<24} {v:>5} wierszy")
    print(f"  trajectories/  {len(list((DST / 'trajectories').iterdir())):>3} plikow")
    print(f"  run_logs/      {len(list((DST / 'run_logs').iterdir())):>3} plikow")
    print(f"  summaries/     {len(list((DST / 'summaries').iterdir())):>3} plikow")
    print(f"  przebiegow: {len(runs)}  (run.log: {n_log}, odtworzone: {n_reeval})")
    print(f"  rozmiar razem: {total:,} B = {total / 1024 / 1024:.2f} MiB")
    print("  walidacja wobec summary.json: WSZYSTKIE komorki zgodne (inaczej byloby przerwanie)")


if __name__ == "__main__":
    main()
