"""L0e rerun analysis (audit 2026-09-07, step 1).

Reads the rerun results under runs/L0e_2026-09/results/{L0e_2026-09,L0_control_2026-09}/<tag>_<repair>/
(run.log, summary.json, trajectories.jsonl), replays the oracle (polagentbench.eval.smoke.evaluate) on every
trajectory and STOPS (exit 2) on any verdict or tag disagreement with run.log / summary.json (rule 4), writes
per-task matrices in the release schema to runs/L0e_2026-09/matrices/, and produces runs/L0e_2026-09/L0E_ANALYSIS.md:
  (1) environment control: same-box original-L0 trajectories vs release_data (raw_model_output identity /80),
  (2) L0 (release) vs L0e paired per instance, tag distribution on L0e, tool calls despite the prohibition,
  (3) Finding 3 with L0e as baseline: exact McNemar L0e vs L3N (strict, typing-corrected) and L0e vs L3T,
      both Bieliks, Q8_0 and Q4_K_M, Holm over the repair=off family.
Run from the repo root with the repo interpreter:  .venv/Scripts/python.exe -B analysis/l0e_analysis.py
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from math import comb
from pathlib import Path

sys.path.insert(0, "src")
from polagentbench.eval.smoke import SmokeStatus, evaluate  # noqa: E402
from polagentbench.io import load_all_tasks  # noqa: E402
from polagentbench.types import Trajectory  # noqa: E402

RESULTS = Path("runs/L0e_2026-09/data")  # the unpacked L0e_2026-09.tgz from the box (results/ is gitignored)
L0E_DIR = RESULTS / "L0e_2026-09"
CTL_DIR = RESULTS / "L0_control_2026-09"
MATRICES = Path("runs/L0e_2026-09/matrices")
REPORT = Path("runs/L0e_2026-09/L0E_ANALYSIS.md")
RELEASE_LADDER = Path("release_data/matrices/per_task_ladder46.csv")
GIT_REF = "8875ef4"

CELLS = [  # tag, model_id, quant, release run prefix
    ("11b_q8", "bielik-11b-v3", "Q8_0", "v3_11b_ladder_2026-07-29__q8"),
    ("11b_q4", "bielik-11b-v3", "Q4_K_M", "v3_11b_ladder_2026-07-29__q4"),
    ("7b_q8", "bielik-minitron-7b-v3", "Q8_0", "v3_7b_ladder_2026-07-29__q8"),
    ("7b_q4", "bielik-minitron-7b-v3", "Q4_K_M", "v3_7b_ladder_2026-07-29__q4"),
]
REPAIRS = ["no_repair", "repair"]
# Typing-corrected L3N passes (repair = off), instances forgiven on top of the strict passes; produced by
# analysis/ladder_typing_tolerant.py and re-derived independently from the trajectories (audit 2026-09-07).
CORRECTED_L3N = {
    ("bielik-11b-v3", "Q8_0"): set("bcefgij"),
    ("bielik-11b-v3", "Q4_K_M"): set("abeh"),
    ("bielik-minitron-7b-v3", "Q8_0"): set("abcdefj"),
    ("bielik-minitron-7b-v3", "Q4_K_M"): set("ei"),
}
SHORT = {"bielik-11b-v3": "11B", "bielik-minitron-7b-v3": "7B"}

TASKS = {}
for d in ("tasks/ladder_l0e", "tasks/ladder_l0_control", "tasks/ladder_ext"):
    for t in load_all_tasks(Path(d)):
        TASKS[t.id] = t

LOGLINE = re.compile(r"^(\S+)\s+([✓✗?])\s+(.*)$")


def mcnemar(n10: int, n01: int) -> float:
    n = n10 + n01
    if n == 0:
        return 1.0
    k = min(n10, n01)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def holm(ps: list[float]) -> list[float]:
    m = len(ps)
    order = sorted(range(m), key=lambda i: ps[i])
    adj = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * ps[i])
        adj[i] = min(1.0, running)
    return adj


def inst(task_id: str) -> str:
    return task_id.rsplit("_", 1)[1]


def read_run_log(path: Path) -> dict[str, tuple[int, set[str]]]:
    out = {}
    for ln in path.read_text(encoding="utf-8").splitlines():
        m = LOGLINE.match(ln)
        if not m:
            continue
        rest = m.group(3)
        tags = set()
        if " - " in rest:
            tags = {x.strip() for x in re.split(r"[;,]\s*", rest.split(" - ", 1)[1]) if x.strip()}
        out[m.group(1)] = (1 if m.group(2) == "✓" else 0, tags)
    return out


def load_run(run_dir: Path) -> list[dict]:
    """Replay the oracle on every trajectory and verify against run.log and summary.json."""
    log = read_run_log(run_dir / "run.log")
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    rows = []
    for ln in (run_dir / "trajectories.jsonl").read_text(encoding="utf-8").splitlines():
        rec = json.loads(ln)
        tr = Trajectory.model_validate(rec)
        sr = evaluate(TASKS[tr.task_id], tr)
        passed = 1 if sr.status is SmokeStatus.PASS else 0
        tags = set(sr.failure_tags)
        lp, ltags = log[tr.task_id]
        if passed != lp or tags != ltags:
            print(f"STOP | oracle replay disagrees with run.log in {run_dir}: {tr.task_id} "
                  f"replay={passed}/{sorted(tags)} log={lp}/{sorted(ltags)}")
            sys.exit(2)
        calls = [s for s in rec["steps"] if (s.get("parsed_action") or {}).get("action") == "call_tool"]
        rows.append({
            "task_id": tr.task_id, "passed": passed, "tags": tags, "steps": len(rec["steps"]),
            "total_tokens": rec.get("total_tokens"), "trajectory_success": int(bool(rec.get("success"))),
            "raw": [s.get("raw_model_output") for s in rec["steps"]], "n_calls": len(calls),
            "seed": rec.get("seed"), "temperature": rec.get("temperature"),
            "final": next(((s.get("parsed_action") or {}).get("answer") for s in reversed(rec["steps"])
                           if (s.get("parsed_action") or {}).get("action") == "final_answer"), None),
        })
    if sum(r["passed"] for r in rows) != summary["num_passed"] or len(rows) != summary["num_tasks"]:
        print(f"STOP | summary.json disagrees with replay in {run_dir}: replay {sum(r['passed'] for r in rows)}/{len(rows)}"
              f" vs summary {summary['num_passed']}/{summary['num_tasks']}")
        sys.exit(2)
    return sorted(rows, key=lambda r: r["task_id"])


def load_release_traj(prefix: str, rep: str) -> dict[str, dict]:
    path = Path("release_data/trajectories") / f"{prefix}_{rep}.jsonl"
    out = {}
    for ln in path.read_text(encoding="utf-8").splitlines():
        rec = json.loads(ln)
        if rec["task_id"].startswith("v3_ext_L0_"):
            out[rec["task_id"]] = {"raw": [s.get("raw_model_output") for s in rec["steps"]],
                                   "total_tokens": rec.get("total_tokens"), "steps": len(rec["steps"])}
    return out


def load_release_ladder() -> dict[tuple, dict[str, tuple[int, set[str]]]]:
    """(model, quant, repair) -> task_id -> (passed, tags) from the released ladder matrix."""
    out = {}
    with RELEASE_LADDER.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            key = (r["model_id"], r["quant"], "repair" if r["repair"] == "on" else "no_repair")
            tags = {t for t in r["failure_tags"].split(";") if t}
            out.setdefault(key, {})[r["task_id"]] = (int(r["passed"]), tags)
    return out


def write_matrix(path: Path, run_id: str, suite: str, model: str, quant: str, rep: str, rows: list[dict], rung: str):
    new = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["run_id", "model_id", "quant", "suite", "repair", "git_ref", "verdict_source", "task_id", "passed",
                        "failure_tags", "steps", "total_tokens", "trajectory_success", "interface_variant", "seed",
                        "temperature", "rung", "instance"])
        for r in rows:
            w.writerow([run_id, model, quant, suite, "on" if rep == "repair" else "off", GIT_REF, "run.log+eval.smoke.evaluate",
                        r["task_id"], r["passed"], ";".join(sorted(r["tags"])), r["steps"], r["total_tokens"],
                        r["trajectory_success"], "PL_EN", r["seed"], r["temperature"], rung, inst(r["task_id"])])


NUM = re.compile(r"-?\d+(?:[.,]\d+)?")


def diagnose(task_id: str, final: str | None, passed: int) -> str:
    """Content diagnosis of an L0/L0e answer: which quantity the model actually computed."""
    if passed:
        return "pass"
    if not final:
        return "no final answer"
    prompt = TASKS[task_id].prompt
    vals = [float(x.replace(",", ".")) for x in NUM.findall(prompt.split("°C")[0].split(":")[-1])]
    if len(vals) != 4:
        return "other"
    mean24 = (vals[1] + vals[3]) / 2
    mean4 = sum(vals) / 4
    f = lambda c: c * 9 / 5 + 32  # noqa: E731
    nums = [float(x.replace(",", ".")) for x in NUM.findall(final)]
    near = lambda target: any(abs(n - target) <= 0.06 for n in nums)  # noqa: E731
    if near(f(mean24)):
        return "gold value present but not accepted"
    if near(mean4) or near(f(mean4)):
        return "averaged all four readings"
    if near(mean24):
        return "right Celsius mean, wrong Fahrenheit"
    return "other value"


def main() -> None:
    MATRICES.mkdir(parents=True, exist_ok=True)
    for f in ("per_task_L0e.csv", "per_task_L0_control.csv"):
        (MATRICES / f).unlink(missing_ok=True)
    release = load_release_ladder()
    out: list[str] = ["# L0e rerun analysis (2026-09-07)\n"]
    l0e: dict[tuple, list[dict]] = {}
    ctl: dict[tuple, list[dict]] = {}

    # ---- replay, matrices, control identity ----
    out.append("## 0. Oracle replay and environment control\n")
    out.append("| cell | repair | L0e pass | L0 control pass | L0 release pass | control raw identical /10 | control tokens equal /10 | control verdict equal /10 |")
    out.append("|---|---|---|---|---|---|---|---|")
    ident_total = 0
    for tag, model, quant, prefix in CELLS:
        for rep in REPAIRS:
            rows_e = load_run(L0E_DIR / f"{tag}_{rep}")
            rows_c = load_run(CTL_DIR / f"{tag}_{rep}")
            l0e[(model, quant, rep)] = rows_e
            ctl[(model, quant, rep)] = rows_c
            write_matrix(MATRICES / "per_task_L0e.csv", f"L0e_2026-09__{tag}_{rep}", "L0e", model, quant, rep, rows_e, "L0e")
            write_matrix(MATRICES / "per_task_L0_control.csv", f"L0_control_2026-09__{tag}_{rep}", "L0_control", model, quant, rep, rows_c, "L0")
            rel_tr = load_release_traj(prefix, rep)
            rel_v = release[(model, quant, rep)]
            ident = sum(1 for r in rows_c if r["raw"] == rel_tr[r["task_id"]]["raw"])
            tok = sum(1 for r in rows_c if r["total_tokens"] == rel_tr[r["task_id"]]["total_tokens"])
            verd = sum(1 for r in rows_c if r["passed"] == rel_v[r["task_id"]][0])
            ident_total += ident
            rel_pass = sum(rel_v[t][0] for t in rel_v if t.startswith("v3_ext_L0_"))
            out.append(f"| {SHORT[model]} {quant} | {rep} | {sum(r['passed'] for r in rows_e)}/10 | {sum(r['passed'] for r in rows_c)}/10 | {rel_pass}/10 | {ident} | {tok} | {verd} |")
    out.append(f"\nOracle replay: every verdict and tag set equals run.log and summary.json in all 16 runs (else this script stops). "
               f"Control trajectories identical in raw_model_output to release_data: **{ident_total}/80**.\n")

    # ---- L0 vs L0e per instance ----
    out.append("## 1. L0 (release, 2026-07-29) vs L0e (explicit prohibition, 2026-09-07), paired per instance\n")
    out.append("| cell | repair | L0 pass | L0e pass | n11 | n10 (L0 only) | n01 (L0e only) | n00 | instances L0e-only | L0e trajectories with any tool call | L0e tag counts |")
    out.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for tag, model, quant, prefix in CELLS:
        for rep in REPAIRS:
            rows_e = l0e[(model, quant, rep)]
            rel_v = release[(model, quant, rep)]
            n11 = n10 = n01 = n00 = 0
            only_e = []
            for r in rows_e:
                a = rel_v["v3_ext_L0_" + inst(r["task_id"])][0]
                b = r["passed"]
                if a and b: n11 += 1
                elif a and not b: n10 += 1
                elif not a and b: n01 += 1; only_e.append(inst(r["task_id"]))
                else: n00 += 1
            tags = Counter(t for r in rows_e for t in r["tags"])
            calls = sum(1 for r in rows_e if r["n_calls"] > 0)
            out.append(f"| {SHORT[model]} {quant} | {rep} | {n11+n10}/10 | {n11+n01}/10 | {n11} | {n10} | {n01} | {n00} | "
                       f"{','.join(only_e) or '-'} | {calls}/10 | {', '.join(f'{k} {v}' for k, v in sorted(tags.items())) or '-'} |")
    out.append("\nReference, L0 release tag counts and tool calls: see per_task_ladder46.csv; L0 control (same box, original prompt) tag counts:\n")
    for tag, model, quant, prefix in CELLS:
        for rep in REPAIRS:
            rows_c = ctl[(model, quant, rep)]
            tags = Counter(t for r in rows_c for t in r["tags"])
            calls = sum(1 for r in rows_c if r["n_calls"] > 0)
            out.append(f"- {SHORT[model]} {quant} {rep}: control tool calls {calls}/10, tags {dict(sorted(tags.items()))}")
    out.append("\nContent diagnosis of L0e answers (what the model computed), per cell:\n")
    out.append("| cell | repair | pass | averaged all four readings | right Celsius mean, wrong Fahrenheit | other value | no final answer |")
    out.append("|---|---|---|---|---|---|---|")
    for tag, model, quant, prefix in CELLS:
        for rep in REPAIRS:
            d = Counter(diagnose(r["task_id"], r["final"], r["passed"]) for r in l0e[(model, quant, rep)])
            out.append(f"| {SHORT[model]} {quant} | {rep} | {d['pass']} | {d['averaged all four readings']} | "
                       f"{d['right Celsius mean, wrong Fahrenheit']} | {d['other value'] + d['other'] + d['gold value present but not accepted']} | {d['no final answer']} |")
    out.append("\nL0e final answers (repair = off), instance: answer:\n")
    for tag, model, quant, prefix in CELLS:
        rows_e = l0e[(model, quant, "no_repair")]
        gold = {r["task_id"]: TASKS[r["task_id"]].expected_final_state.get("final_answer_contains_any") for r in rows_e}
        out.append(f"- **{SHORT[model]} {quant}**: " + "; ".join(
            f"{inst(r['task_id'])} [{'P' if r['passed'] else 'F'}, gold {gold[r['task_id']][0] if gold[r['task_id']] else '?'}] "
            f"{(r['final'] or '<no final answer>')[:70]!r}" for r in rows_e))

    # ---- Finding 3 with L0e baseline ----
    out.append("\n## 2. Finding 3 with L0e as the baseline (exact two-sided McNemar, instance-paired)\n")
    fam = []  # (label, n11, n10, n01, n00, p) for repair off
    for rep in REPAIRS:
        out.append(f"\n### repair = {'off' if rep == 'no_repair' else 'on'}\n")
        out.append("| model | precision | contrast | rate | L0e | rung | n11 | n10 | n01 | n00 | p |")
        out.append("|---|---|---|---|---|---|---|---|---|---|---|")
        for tag, model, quant, prefix in CELLS:
            rel_v = release[(model, quant, rep)]
            e = {inst(r["task_id"]): r["passed"] for r in l0e[(model, quant, rep)]}
            l3n = {inst(t): v[0] for t, v in rel_v.items() if t.startswith("v3_ext_L3N_")}
            l3t = {inst(t): v[0] for t, v in rel_v.items() if t.startswith("v3_ext_L3T_")}
            contrasts = [("L0e vs L3N", "strict", l3n)]
            if rep == "no_repair":
                l3n_c = {k: (1 if (v or k in CORRECTED_L3N[(model, quant)]) else 0) for k, v in l3n.items()}
                contrasts.append(("L0e vs L3N", "corrected", l3n_c))
            contrasts.append(("L0e vs L3T", "strict", l3t))
            for name, rate, rung in contrasts:
                keys = sorted(rung)
                n11 = sum(1 for k in keys if e[k] and rung[k]); n10 = sum(1 for k in keys if e[k] and not rung[k])
                n01 = sum(1 for k in keys if not e[k] and rung[k]); n00 = sum(1 for k in keys if not e[k] and not rung[k])
                p = mcnemar(n10, n01)
                out.append(f"| {SHORT[model]} | {quant} | {name} (n={len(keys)}) | {rate} | {n11+n10}/{len(keys)} | {n11+n01}/{len(keys)} | {n11} | {n10} | {n01} | {n00} | {p:.4g} |")
                if rep == "no_repair":
                    fam.append((f"{SHORT[model]} {quant} {name} {rate}", p))
    adj = holm([p for _, p in fam])
    out.append("\n### Holm within the repair = off family (12 tests)\n")
    out.append("| test | raw p | Holm p | significant at 0.05 |")
    out.append("|---|---|---|---|")
    for (label, p), a in zip(fam, adj):
        out.append(f"| {label} | {p:.4g} | {a:.4g} | {'yes' if a < 0.05 else 'no'} |")
    REPORT.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
