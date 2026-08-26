"""Tabele trybow porazki i kosztu trajektorii: tab:purity, tab:modes, tab:tokens, tab:tokens-full.

CO LICZY:
Dla wszystkich 18 komorek krzywej glownej (3 modele x 6 kwantow, suite main67, repair=off)
liczy cztery rzeczy naraz:
  * Tab 1 (tab:purity)       - porazki na 25 zadaniach arytmetycznych i ile z nich jest
                               jednokategoryjnych (dokladnie jedna galaz klasyfikatora aktywna),
  * Tab 3 (tab:modes)        - te same porazki w rozbiciu PROTOCOL_SHAPE / GENUINE_ARITH /
                               TOOL_FIXATION, plus ROUNDING_MINE, ktory pada dokladnie raz
                               w calej siatce, na 7B Q5_K_M,
  * Tab 4 (tab:tokens)       - mediany tokenow i krokow wg werdyktu, para Bielikow,
  * Tab 19 (tab:tokens-full) - n, srednia, mediana, p90 tokenow oraz srednia i mediana krokow.

Werdykty pochodza WYLACZNIE z oracle'a (eval.smoke.evaluate), nigdy z flagi
trajectory.success - ta na PLLuM Q8 daje 66/67 wobec 13/67 oracle'a.
Etykiety pochodza z analysis/failure_classifier.py, czyli z kanonicznego klasyfikatora.

BRAMKA: skrypt sam sprawdza sie wobec liczb opublikowanych w paperze (36 komorek wpisanych
recznie w PUBLISHED_* ponizej) i konczy sie kodem 1 przy jakimkolwiek rozjezdzie. Komorki
7B Q6_K i Q5_K_M, w paperze puste do 2026-08-26, zostaly dopisane wlasnie tym skryptem,
po tym jak przeszedl bramke na wszystkich pozostalych. Wypisuje je z etykieta NOWA.

WYBOR RUNOW: dla kazdej pary (model, kwant) musi istniec DOKLADNIE JEDEN run. Runy
v3_11b_variance_* sa wykluczone - to sonda wariancji przy T=0.7 (Tab 9), nie krzywa glowna,
a w runs.csv maja ten sam model, kwant, suite i repair co komorki Q8_0 i Q3_K_M dla 11B.
Skrypt dodatkowo sprawdza, ze kazda czytana trajektoria ma temperature 0.

ZRODLO DANYCH: release_data/ (opublikowane), nie results/. Ten skrypt dziala wiec
z samego klona repo, bez surowych katalogow runow.

TYLKO ODCZYT - nie zapisuje niczego.
Uzycie:
  .venv/Scripts/python.exe analysis/mode_tables.py
"""

from __future__ import annotations

import contextlib
import csv
import json
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "analysis")

from failure_classifier import active_branches, classify_failure, is_arith_task

from polagentbench.eval.smoke import SmokeStatus, evaluate
from polagentbench.io import load_all_tasks
from polagentbench.protocol import FinalAnswer
from polagentbench.types import Trajectory

QUANTS = ["Q8_0", "Q6_K", "Q5_K_M", "Q4_K_M", "Q3_K_M", "Q2_K"]
M7, M11, MP = "bielik-minitron-7b-v3", "bielik-11b-v3", "llama-pllum-8b"
MODELS = [M7, M11, MP]
SHORT = {M7: "7B", M11: "11B", MP: "PLLuM"}

# Liczby przepisane recznie z papera. Sluza jako bramka, nie jako zrodlo.
# (porazki, jednokategoryjne, protocol, arith, fixation)
PUBLISHED_MODES = {
    (M7, "Q8_0"): (21, 1, 16, 4, 1),
    (M7, "Q4_K_M"): (21, 5, 7, 13, 1),
    (M7, "Q3_K_M"): (20, 13, 5, 4, 11),
    (M7, "Q2_K"): (25, 7, 6, 15, 4),
    (M11, "Q8_0"): (11, 3, 5, 4, 2),
    (M11, "Q6_K"): (10, 3, 3, 5, 2),
    (M11, "Q5_K_M"): (11, 4, 4, 6, 1),
    (M11, "Q4_K_M"): (17, 2, 9, 7, 1),
    (M11, "Q3_K_M"): (10, 8, 0, 7, 3),
    (M11, "Q2_K"): (25, 3, 5, 19, 1),
    (MP, "Q8_0"): (23, 6, 0, 23, 0),
    (MP, "Q6_K"): (23, 9, 0, 22, 1),
    (MP, "Q5_K_M"): (24, 6, 4, 20, 0),
    (MP, "Q4_K_M"): (23, 4, 1, 22, 0),
    (MP, "Q3_K_M"): (22, 9, 1, 20, 1),
    (MP, "Q2_K"): (25, 5, 0, 23, 2),
}

# (n, srednia tok., mediana tok., p90 tok., srednia krokow, mediana krokow), pass i fail.
PUBLISHED_TOKENS = {
    (M7, "Q8_0"): ((30, 4540, 3504, 8645, 3.30, 3.0), (37, 12346, 12298, 17219, 7.27, 8.0)),
    (M7, "Q4_K_M"): ((34, 4857, 3501, 11281, 3.24, 3.0), (33, 12920, 10793, 21006, 6.30, 6.0)),
    (M7, "Q3_K_M"): ((31, 4766, 3509, 9844, 3.23, 3.0), (36, 22362, 26833, 37766, 7.22, 8.0)),
    (M7, "Q2_K"): ((10, 4158, 3230, 6368, 2.40, 2.0), (57, 13795, 9139, 32161, 4.70, 4.0)),
    (M11, "Q8_0"): ((54, 6309, 5914, 10381, 4.33, 4.5), (13, 8473, 8415, 12806, 5.62, 6.0)),
    (M11, "Q6_K"): ((56, 6173, 6378, 9675, 4.30, 4.5), (11, 7579, 7510, 12856, 5.09, 5.0)),
    (M11, "Q5_K_M"): ((50, 6220, 5186, 10691, 4.30, 4.0), (17, 8742, 7510, 15398, 5.59, 5.0)),
    (M11, "Q4_K_M"): ((36, 5432, 3561, 10442, 3.72, 3.0), (31, 9580, 10849, 14254, 5.77, 6.0)),
    (M11, "Q3_K_M"): ((48, 5775, 5228, 8959, 4.21, 4.0), (19, 7819, 6693, 12739, 5.11, 5.0)),
    (M11, "Q2_K"): ((3, 5629, 4010, 10240, 3.33, 3.0), (64, 5386, 1506, 14650, 2.75, 1.0)),
}


def p90(values):
    """Percentyl 90 z interpolacja liniowa, ta sama konwencja co numpy.percentile."""
    values = sorted(values)
    k = 0.9 * (len(values) - 1)
    lo = int(k)
    hi = min(lo + 1, len(values) - 1)
    return values[lo] + (k - lo) * (values[hi] - values[lo])


def goldens(task):
    """Wartosci goldenu zadania jako floaty, z final_answer_contains_any."""
    spec = (task.expected_final_state or {}).get("final_answer_contains_any") or []
    out = []
    for entry in spec:
        for match in re.findall(r"-?\d+[.,]?\d*", str(entry)):
            with contextlib.suppress(ValueError):
                out.append(float(match.replace(",", ".")))
    return out


def final_answer_text(trajectory):
    """Tekst final_answer, tak jak widzi go oracle: pierwsza sparsowana akcja tego typu."""
    for step in trajectory.steps:
        if isinstance(step.parsed_action, FinalAnswer):
            return step.parsed_action.answer
    return ""


def pick_runs():
    """Dokladnie jeden run na komorke krzywej glownej, 18 komorek."""
    with open("release_data/matrices/runs.csv", encoding="utf-8") as handle:
        rows = [
            row
            for row in csv.DictReader(handle)
            if row["suite"] == "main67"
            and row["repair"] == "off"
            and "variance" not in row["run_id"]
        ]
    runs = {}
    for row in rows:
        key = (row["model_id"], row["quant"])
        if key in runs:
            raise SystemExit(f"dwa runy na komorke {key}: {runs[key]['run_id']} i {row['run_id']}")
        runs[key] = row
    if len(runs) != 18:
        raise SystemExit(f"oczekiwano 18 komorek, jest {len(runs)}")
    return runs


def measure(run, tasks):
    """Jedna komorka: werdykty oracle, etykiety klasyfikatora, tokeny i kroki."""
    path = Path("release_data/trajectories") / f"{run['run_id']}.jsonl"
    labels = dict.fromkeys(
        ["PROTOCOL_SHAPE", "GENUINE_ARITH", "TOOL_FIXATION", "ROUNDING_MINE", "other"], 0
    )
    tokens = {"pass": [], "fail": []}
    steps = {"pass": [], "fail": []}
    arith_fails = single = n_pass = n_all = 0

    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            if (record.get("temperature") or 0) != 0.0:
                raise SystemExit(f"{run['run_id']}: temperature != 0, to nie krzywa glowna")
            task = tasks[record["task_id"]]
            trajectory = Trajectory.model_validate(record)
            result = evaluate(task, trajectory)
            passed = result.status is SmokeStatus.PASS
            n_all += 1
            n_pass += passed
            bucket = "pass" if passed else "fail"
            tokens[bucket].append(record.get("total_tokens") or 0)
            steps[bucket].append(len(trajectory.steps))
            if not passed and is_arith_task(record["task_id"]):
                arith_fails += 1
                label = classify_failure(
                    result.failure_tags, final_answer_text(trajectory), goldens(task)
                )
                labels[label] += 1
                single += sum(active_branches(result.failure_tags)) == 1

    if n_pass != int(run["num_passed"]) or n_all != int(run["num_tasks"]):
        raise SystemExit(
            f"{run['run_id']}: oracle {n_pass}/{n_all}, "
            f"runs.csv {run['num_passed']}/{run['num_tasks']}"
        )
    return {
        "arith_fails": arith_fails,
        "single": single,
        "labels": labels,
        "tokens": tokens,
        "steps": steps,
    }


def stats(tokens, steps):
    return (
        len(tokens),
        round(statistics.mean(tokens)),
        round(statistics.median(tokens)),
        round(p90(tokens)),
        round(statistics.mean(steps), 2),
        float(statistics.median(steps)),
    )


def main():
    tasks = {t.id: t for t in load_all_tasks(Path("tasks/adversarial"))}
    runs = pick_runs()
    cells = {key: measure(run, tasks) for key, run in runs.items()}
    mismatches = []

    print("=== Tab 1 (tab:purity) i Tab 3 (tab:modes), 25 zadan arytmetycznych ===")
    print(
        f"{'model':<7}{'kwant':<9}{'porazek':>8}{'jednokat.':>11}"
        f"{'protocol':>10}{'arith':>7}{'fixation':>10}{'rounding':>10}  bramka"
    )
    for model in MODELS:
        for quant in QUANTS:
            cell = cells[(model, quant)]
            lab = cell["labels"]
            got = (
                cell["arith_fails"],
                cell["single"],
                lab["PROTOCOL_SHAPE"],
                lab["GENUINE_ARITH"],
                lab["TOOL_FIXATION"],
            )
            expected = PUBLISHED_MODES.get((model, quant))
            if expected is None:
                gate = "NOWA"
            elif got == expected:
                gate = "ok"
            else:
                gate = f"ROZJAZD, w paperze {expected}"
                mismatches.append(f"modes {SHORT[model]} {quant}: {got} != {expected}")
            print(
                f"{SHORT[model]:<7}{quant:<9}{got[0]:>8}{got[1]:>11}"
                f"{got[2]:>10}{got[3]:>7}{got[4]:>10}{lab['ROUNDING_MINE']:>10}  {gate}"
            )
            if lab["other"]:
                mismatches.append(
                    f"kategoria other niepusta: {SHORT[model]} {quant} = {lab['other']}"
                )

    print()
    print("=== Tab 19 (tab:tokens-full) i Tab 4 (tab:tokens, kolumny median) ===")
    print(
        f"{'model':<7}{'kwant':<9}{'wynik':<6}{'n':>4}{'sr.tok':>9}{'med.tok':>9}"
        f"{'p90 tok':>9}{'sr.kr.':>8}{'med.kr.':>9}  bramka"
    )
    for model in (M7, M11):
        for quant in QUANTS:
            cell = cells[(model, quant)]
            expected_pair = PUBLISHED_TOKENS.get((model, quant))
            for index, bucket in enumerate(("pass", "fail")):
                got = stats(cell["tokens"][bucket], cell["steps"][bucket])
                if expected_pair is None:
                    gate = "NOWA"
                elif got == expected_pair[index]:
                    gate = "ok"
                else:
                    gate = f"ROZJAZD, w paperze {expected_pair[index]}"
                    mismatches.append(
                        f"tokens {SHORT[model]} {quant} {bucket}: {got} != {expected_pair[index]}"
                    )
                print(
                    f"{SHORT[model]:<7}{quant:<9}{bucket:<6}{got[0]:>4}{got[1]:>9}"
                    f"{got[2]:>9}{got[3]:>9}{got[4]:>8}{got[5]:>9}  {gate}"
                )

    print()
    if mismatches:
        print(f"BRAMKA NIE PRZESZLA, rozjazdow: {len(mismatches)}")
        for line in mismatches:
            print("  " + line)
        return 1
    checked = len(PUBLISHED_MODES) + 2 * len(PUBLISHED_TOKENS)
    print(f"BRAMKA OK: {checked} opublikowanych komorek odtworzonych co do jednego.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
