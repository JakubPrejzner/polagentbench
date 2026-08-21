# -*- coding: utf-8 -*-
"""
Envelope collapse: rozklady brzegowe i ilorazy ryzyka - narzedzie wobec pozycji.

CO LICZY:
Liczy P(zla koperta | convert_temperature) wobec P(zla | inne narzedzie) oraz
P(zla | trzeci krok) wobec P(zla | inna pozycja), i ilorazy ryzyka dla obu zmiennych.
Dla PLLuM: narzedzie 3.95x, pozycja 0.60x, czyli dominuje narzedzie, a trzeci krok jest
wrecz bezpieczniejszy od sredniej. Dla obu runow Bielika-7B zadna ze zmiennych nie tlumaczy
niczego. Klasyfikuje tez 5 przypadkow 'brak pola action' - okazuja sie gole obiekty
{answer: ...} bez koperty, a nie proby wywolania convert.

CZYTA Z:
  jak w envelope_positions.py

PRODUKUJE:
  Sesja 3, Analiza 3: TABELA 3d.

TYLKO ODCZYT - skrypt niczego nie zapisuje ani nie modyfikuje.
Uruchamiac z katalogu glownego repo:
  .venv/Scripts/python.exe analysis/envelope_marginals.py
"""
import json,sys,re
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
RUNS={"PLLuM-8B Q8 main":"results/v3_pllum_2026-07-29/q8_main_no_repair",
      "Bielik-7B Q8 main (arith_clean)":"results/v3_arith_clean_2026-06-18/q8_no_repair",
      "Bielik-7B Q8 main (ladder0611)":"results/v3_ladder_2026-06-11/q8_no_repair"}
def flat_name(raw):
    m=re.search(r'"action"\s*:\s*"([^"]+)"',raw); return m.group(1) if m else None

print("=== 5 krokow PLLuM 'brak pola action' — co model naprawde probowal wywolac ===")
RUN=RUNS["PLLuM-8B Q8 main"]
for l in open(f"{RUN}/trajectories.jsonl",encoding="utf-8"):
    t=json.loads(l)
    for s in t["steps"]:
        if s["parse_error"] and s["parse_error"]["category"]=="unknown_action" and flat_name(s["raw_model_output"]) is None:
            print(f"  {t['task_id']:<24} k{s['step_idx']}  {s['raw_model_output'][:150]}")
print()
for label,RUN in RUNS.items():
    trajs=[json.loads(l) for l in open(f"{RUN}/trajectories.jsonl",encoding="utf-8")]
    steps=[s for t in trajs for s in t["steps"]]
    def conv(s):
        pa=s["parsed_action"] or {}
        if pa.get("action")=="call_tool": return pa.get("tool")=="convert_temperature"
        if s["parse_error"] and s["parse_error"]["category"]=="unknown_action":
            fn=flat_name(s["raw_model_output"])
            if fn=="convert_temperature": return True
            if fn is None: return '"value"' in s["raw_model_output"] and "unit" in s["raw_model_output"]
        return False
    def bad(s): return s["parse_error"] is not None
    def rate(sel):
        g=[s for s in steps if sel(s)]
        return (sum(1 for s in g if bad(s)), len(g))
    bc,nc = rate(conv); bn,nn = rate(lambda s: not conv(s))
    b3,n3 = rate(lambda s: s["step_idx"]==2); bo,no = rate(lambda s: s["step_idx"]!=2)
    print(f"### {label}   krokow={len(steps)}  bledow parsowania={sum(1 for s in steps if bad(s))}")
    print(f"{'':>4}{'warunek':<34}{'zlych/wszystkich':>20}{'udzial zlych':>14}")
    print("-"*74)
    print(f"{'':>4}{'narzedzie = convert_temperature':<34}{f'{bc}/{nc}':>20}{(bc/nc if nc else 0):>13.1%}")
    print(f"{'':>4}{'narzedzie != convert_temperature':<34}{f'{bn}/{nn}':>20}{(bn/nn if nn else 0):>13.1%}")
    r1=(bc/nc)/(bn/nn) if nc and nn and bn else float('nan')
    print(f"{'':>4}{'  -> iloraz ryzyka (narzedzie)':<34}{'':>20}{r1:>13.2f}x")
    print(f"{'':>4}{'pozycja = trzeci krok':<34}{f'{b3}/{n3}':>20}{(b3/n3 if n3 else 0):>13.1%}")
    print(f"{'':>4}{'pozycja != trzeci krok':<34}{f'{bo}/{no}':>20}{(bo/no if no else 0):>13.1%}")
    r2=(b3/n3)/(bo/no) if n3 and no and bo else float('nan')
    print(f"{'':>4}{'  -> iloraz ryzyka (pozycja)':<34}{'':>20}{r2:>13.2f}x")
    print()
