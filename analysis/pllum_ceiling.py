# -*- coding: utf-8 -*-
"""
PLLuM: uczciwy sufit - kaskada formatu wobec czystej niezdolnosci.

CO LICZY:
Klasyfikuje porazki obu modeli na A (czysty format), B (format i tresc, kaskada mozliwa),
C (wylacznie tresc, zero bledow formatu) i liczy dwa sufity: ostrozny i hojny. Liczba
rozstrzygajaca: nawet po darowaniu PLLuM kazdej porazki dotknietej bledem formatu sufit
wynosi 32/67 = 0.478, ponizej faktycznego 0.806 Bielika. 35 z 54 porazek PLLuM nie ma
bledu formatu w ogole.

CZYTA Z:
  release_data/matrices/per_task_main67.csv (main67, Q8_0, repair=off; werdykty oracle)

PRODUKUJE:
  Sesja 2, Analiza 1: TABELA 1d.

TYLKO ODCZYT - skrypt niczego nie zapisuje ani nie modyfikuje.
Uruchamiac z katalogu glownego repo:
  .venv/Scripts/python.exe -B analysis/pllum_ceiling.py
"""
import sys, csv
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FORMAT = {"unknown_action","no_json_found","invalid_json","schema_violation",
          "final_answer_shape_violation","final_answer_missing"}
CONTENT= {"wrong_final_answer","wrong_tool_order","expected_tool_not_called",
          "unexpected_tool_call","unauthorized_side_effect","hallucinated_tool_result",
          "tool_call_failed","timeout"}

def released_verdicts(model_id):
    with open("release_data/matrices/per_task_main67.csv", encoding="utf-8") as fh:
        return {
            r["task_id"]: (
                "PASS" if r["passed"] == "1" else "FAIL",
                {t for t in r["failure_tags"].split(";") if t},
            )
            for r in csv.DictReader(fh)
            if r["model_id"] == model_id and r["suite"] == "main67"
            and r["quant"] == "Q8_0" and r["repair"] == "off"
        }

def pv():
    return released_verdicts("llama-pllum-8b")
def bv():
    return released_verdicts("bielik-11b-v3")

for label, verds, total in (("PLLuM-8B Q8_0", pv(), 67), ("Bielik-11B Q8_0", bv(), 67)):
    A=B=C=0; exC=[]
    for tid,(st,tg) in verds.items():
        if st!="FAIL": continue
        f, c = tg & FORMAT, tg & CONTENT
        if c and not f: C+=1; exC.append((tid,sorted(c)))
        elif c and f:   B+=1
        else:           A+=1
    p = total - (A+B+C)
    print(f"### {label}   PASS={p}/{total} ({p/total:.3f})   porazek={A+B+C}")
    print(f"   A. czysto FORMAT (bez tagu tresci)                    {A:>3}")
    print(f"   B. format + tresc  (kaskada mozliwa)                  {B:>3}")
    print(f"   C. TYLKO tresc, zero bledow formatu (twarda porazka)  {C:>3}")
    print(f"   -> sufit ostrozny (darowane A)          {p+A}/{total} = {(p+A)/total:.3f}")
    print(f"   -> sufit HOJNY   (darowane A i cale B)  {p+A+B}/{total} = {(p+A+B)/total:.3f}   <-- gorna granica 'gdyby format byl idealny'")
    print(f"   -> nieusuwalne porazki merytoryczne (C): {C}")
    if label.startswith("PLLuM"):
        print("      przyklady C:", ", ".join(f"{t}[{'|'.join(g)}]" for t,g in exC[:8]))
    print()
