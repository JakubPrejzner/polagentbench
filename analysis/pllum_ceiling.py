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
  jak w pllum_vs_bielik.py

PRODUKUJE:
  Sesja 2, Analiza 1: TABELA 1d.

TYLKO ODCZYT - skrypt niczego nie zapisuje ani nie modyfikuje.
Uruchamiac z katalogu glownego repo:
  .venv/Scripts/python.exe analysis/pllum_ceiling.py
"""
import json, re, sys, csv
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FORMAT = {"unknown_action","no_json_found","invalid_json","schema_violation",
          "final_answer_shape_violation","final_answer_missing"}
CONTENT= {"wrong_final_answer","wrong_tool_order","expected_tool_not_called",
          "unexpected_tool_call","unauthorized_side_effect","hallucinated_tool_result",
          "tool_call_failed","timeout"}

def pv():
    v={}
    for ln in open("results/v3_pllum_2026-07-29/q8_main_no_repair/run.log",encoding="utf-8"):
        m=re.match(r"^(\S+)\s+([✓✗?])\s+(.*)$",ln.rstrip("\n"))
        if m:
            tail=m.group(3); tags=set()
            if " - " in tail: tags={t.strip() for t in tail.rsplit(" - ",1)[1].split(",")}
            v[m.group(1)]=("PASS" if m.group(2)=="✓" else "FAIL",tags)
    return v
def bv():
    return {r["task_id"]:(r["q8_no_repair"],{t for t in (r["tags_q8_no_repair"] or "").split(";") if t})
            for r in csv.DictReader(open("results/v3_11b_2026-06-18/analysis/per_task_matrix.csv",encoding="utf-8"))}

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
