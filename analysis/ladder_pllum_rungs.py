"""
Drabina, PLLuM: rozbicie na szczeble L0/L1/L2/L3T/L3N dla szesciu kwantow.

CO LICZY:
Dla szesciu runow drabiny llama-pllum-8b (Q8_0, Q6_K, Q5_K_M, Q4_K_M, Q3_K_M, Q2_K, repair off)
liczy zaliczenia osobno dla L0, L1, L2, L3T i L3N. Uzupelnia ladder_breakdown.py, ktory pokrywa
wylacznie osiem komorek Bielika. Werdykty pochodza WYLACZNIE z oracle'a (znacznik w run.log),
nigdy z trajectory.success. Przypisanie zadania do szczebla jest to samo co w ladder_breakdown.py
(prefiks id zadania). Kolumna RAZEM sluzy jako kontrola poprawnosci odczytu - liczba zadan
w komorce musi wynosic 46, a suma zaliczen musi zgadzac sie z num_passed w summary.json.

Liczba rozstrzygajaca: jedyne dwa zaliczenia PLLuM na calej drabinie to Q8_0 na szczeblu L0
(zadania v3_ext_L0_c i v3_ext_L0_f); piec pozostalych kwantow ma 0/46.

CZYTA Z:
  results/v3_pllum_2026-07-29/q{8,6,5,4,3,2}_ladder_no_repair/{run.log,summary.json}

PRODUKUJE:
  paper/tables/ladder.tex - szesc wierszy Llama-PLLuM-8B.

TYLKO ODCZYT - skrypt niczego nie zapisuje ani nie modyfikuje.
Uruchamiac z katalogu glownego repo:
  .venv/Scripts/python.exe analysis/ladder_pllum_rungs.py
"""
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RUNS = [
    ("Q8_0", "results/v3_pllum_2026-07-29/q8_ladder_no_repair"),
    ("Q6_K", "results/v3_pllum_2026-07-29/q6_ladder_no_repair"),
    ("Q5_K_M", "results/v3_pllum_2026-07-29/q5_ladder_no_repair"),
    ("Q4_K_M", "results/v3_pllum_2026-07-29/q4_ladder_no_repair"),
    ("Q3_K_M", "results/v3_pllum_2026-07-29/q3_ladder_no_repair"),
    ("Q2_K", "results/v3_pllum_2026-07-29/q2_ladder_no_repair"),
]

RUNGS = ["L0", "L1", "L2", "L3T", "L3N"]


def rung(tid):
    """Przypisanie zadania do szczebla - identyczne z analysis/ladder_breakdown.py."""
    m = re.match(r"v3_ext_(L3N|L3T|L0|L1|L2)_", tid)
    return m.group(1) if m else None


def verdicts(run):
    """Werdykty oracle z run.log - parsowanie jak w analysis/pllum_ceiling.py."""
    v = {}
    with open(f"{run}/run.log", encoding="utf-8") as fh:
        for ln in fh:
            m = re.match(r"^(\S+)\s+([✓✗?])\s+(.*)$", ln.rstrip("\n"))
            if m:
                tail = m.group(3)
                tags = set()
                if " - " in tail:
                    tags = {t.strip() for t in tail.rsplit(" - ", 1)[1].split(",")}
                v[m.group(1)] = ("PASS" if m.group(2) == "✓" else "FAIL", tags)
    return v


def num_passed(run):
    with open(f"{run}/summary.json", encoding="utf-8") as fh:
        return json.load(fh)["num_passed"]


DATA = {}
PASSED_IDS = {}
for quant, run in RUNS:
    v = verdicts(run)
    per = {r: [0, 0] for r in RUNGS}
    passed = []
    for tid, (st, _tags) in v.items():
        r = rung(tid)
        if r is None:
            continue
        per[r][1] += 1
        if st == "PASS":
            per[r][0] += 1
            passed.append(tid)
    DATA[quant] = per
    PASSED_IDS[quant] = sorted(passed)

print("Llama-PLLuM-8B, suita ladder46 - zaliczenia per szczebel (repair OFF, T=0, seed=42)")
head = f"{'kwant':<9}"
for r in RUNGS:
    head += f"{r + ' (n=' + str(DATA['Q8_0'][r][1]) + ')':>13}"
print(head + f"{'RAZEM':>10}")
print("-" * (9 + 13 * len(RUNGS) + 10))
for quant, _run in RUNS:
    per = DATA[quant]
    tp = sum(p for p, _ in per.values())
    tt = sum(t for _, t in per.values())
    cells = "".join(f"{f'{per[r][0]}/{per[r][1]}':>13}" for r in RUNGS)
    print(f"{quant:<9}{cells}{f'{tp}/{tt}':>10}")

print()
print("KONTROLA - suma per komorka wobec summary.json")
ok = True
for quant, run in RUNS:
    per = DATA[quant]
    tp = sum(p for p, _ in per.values())
    tt = sum(t for _, t in per.values())
    n = num_passed(run)
    good = tt == 46 and tp == n
    ok = ok and good
    mark = "OK " if good else "ROZJAZD"
    print(f"   {mark} {quant:<8} zadan={tt:<3} (oczekiwane 46)   passed={tp}   num_passed={n}")

print()
print("KONTROLA - id zaliczonych zadan (oracle)")
for quant, _run in RUNS:
    ids = PASSED_IDS[quant]
    print(f"   {quant:<8} {', '.join(ids) if ids else '(brak)'}")

print()
print("WYNIK KONTROLI:", "wszystko zgodne" if ok else "SA ROZJAZDY - nie uzywac liczb")
