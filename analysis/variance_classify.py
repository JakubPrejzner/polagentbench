# -*- coding: utf-8 -*-
"""
Wariancja: klasyfikacja A/B/C i sufity dla szesciu runow seedowych.

CO LICZY:
Liczy dla kazdego seeda udzial krokow, ktore nie parsuja sie, oraz sufit hojny. Liczba do
papera: po darowaniu wszystkich porazek z tagiem formatu seed1 laduje na 0.776 (Q8) i 0.881 (Q3).
To gorne granice, nie odzyskane wyniki: na Q3 w pasmie analogicznych sufitow seedow 2 i 3, na Q8
ponizej. Zapasc seed1 wiaze sie z porazkami z tagiem formatu; te granice nie ustalaja, czy format
degraduje sie przed rozumowaniem (paper, par. 9 i App. K). Zbior FORMAT obejmuje final_answer_missing,
ktory w taksonomii par. 3.7 jest tagiem tool fixation.

CZYTA Z:
  results/v3_11b_variance_2026-07-29/*/{run.log,trajectories.jsonl}

PRODUKUJE:
  Sesja 2, Analiza 2: TABELA 2c.

TYLKO ODCZYT - skrypt niczego nie zapisuje ani nie modyfikuje.
Uruchamiac z katalogu glownego repo:
  .venv/Scripts/python.exe analysis/variance_classify.py
"""
import json,re,sys,collections
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
BASE="results/v3_11b_variance_2026-07-29"
FORMAT={"unknown_action","no_json_found","invalid_json","schema_violation",
        "final_answer_shape_violation","final_answer_missing"}
CONTENT={"wrong_final_answer","wrong_tool_order","expected_tool_not_called",
         "unexpected_tool_call","unauthorized_side_effect","hallucinated_tool_result",
         "tool_call_failed","timeout","loop"}
def verd(r):
    v={}
    for ln in open(f"{BASE}/{r}/run.log",encoding="utf-8"):
        m=re.match(r"^(\S+)\s+([✓✗?])\s+(.*)$",ln.rstrip("\n"))
        if m:
            tail=m.group(3); tg=set()
            if " - " in tail: tg={t.strip() for t in tail.rsplit(" - ",1)[1].split(",")}
            v[m.group(1)]=("PASS" if m.group(2)=="✓" else "FAIL",tg)
    return v
print(f"{'run':<10}{'PASS':>8}{'A czysty':>10}{'B kaskada':>11}{'C twarda':>10}{'sufit ostrozny':>17}{'sufit hojny':>14}")
print(f"{'':<10}{'':>8}{'format':>10}{'fmt+tresc':>11}{'tresc':>10}{'(A darowane)':>17}{'(A+B)':>14}")
print("-"*80)
for r in ["q8_seed1","q8_seed2","q8_seed3","q3_seed1","q3_seed2","q3_seed3"]:
    v=verd(r); A=B=C=0
    for tid,(st,tg) in v.items():
        if st!="FAIL": continue
        f,c=tg&FORMAT,tg&CONTENT
        if c and not f: C+=1
        elif c and f:   B+=1
        else:           A+=1
    p=67-(A+B+C)
    print(f"{r:<10}{str(p)+'/67':>8}{A:>10}{B:>11}{C:>10}"
          f"{str(p+A)+'/67 = '+format((p+A)/67,'.3f'):>17}{str(p+A+B)+'/67 = '+format((p+A+B)/67,'.3f'):>14}")

print()
print("Ile krokow na trajektorie NIE parsuje sie (dyscyplina koperty), a ile trescia sie rozni:")
print(f"{'run':<10}{'krokow':>9}{'bledy parsowania':>19}{'udzial':>9}{'traj. na max_steps':>21}")
print("-"*70)
for r in ["q8_seed1","q8_seed2","q8_seed3","q3_seed1","q3_seed2","q3_seed3"]:
    tr=[json.loads(l) for l in open(f"{BASE}/{r}/trajectories.jsonl",encoding="utf-8")]
    st=[s for t in tr for s in t["steps"]]
    bad=sum(1 for s in st if s["parse_error"])
    mx=sum(1 for t in tr if len(t["steps"])>=8)
    print(f"{r:<10}{len(st):>9}{bad:>19}{bad/len(st):>8.1%}{mx:>21}")
