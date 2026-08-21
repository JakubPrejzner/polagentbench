# -*- coding: utf-8 -*-
"""
Atraktor 59: pierwszy surowy skan zbioru. UWAGA - zlicza obiekty JSON, nie zadania.

CO LICZY:
Skanuje wszystkie trajektorie i zbiera liczbowe final_answer. Ten skrypt liczy KAZDY obiekt
JSON osobno, a model powtarza te sama odpowiedz przez wiele krokow, wiec wyniki sa ZAWYZONE
(61 wychodzi 4189 razy, a odpowiada 32 parom run-zadanie). Zachowany, bo to on wykryl, ze
czolowka najczestszych wartosci to dokladne konwersje C->F. Do liczb raportowanych uzywac
attractor59_count.py, ktory zlicza unikalne pary (run, zadanie).

CZYTA Z:
  results/**/trajectories.jsonl, results/**/summary.json

PRODUKUJE:
  Sesja 3, Analiza 2: material pomocniczy, NIE zrodlo liczb w tabelach.

TYLKO ODCZYT - skrypt niczego nie zapisuje ani nie modyfikuje.
Uruchamiac z katalogu glownego repo:
  .venv/Scripts/python.exe analysis/attractor59_scan_raw.py
"""
import json, sys, glob, os, collections, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
def json_objects(text):
    out,depth,start,instr,esc=[],0,None,False,False
    for i,ch in enumerate(text):
        if instr:
            if esc: esc=False
            elif ch==chr(92): esc=True
            elif ch=='"': instr=False
            continue
        if ch=='"': instr=True; continue
        if ch=="{":
            if depth==0: start=i
            depth+=1
        elif ch=="}":
            if depth>0:
                depth-=1
                if depth==0 and start is not None:
                    try: out.append(json.loads(text[start:i+1]))
                    except Exception: pass
                    start=None
    return out
hits=collections.defaultdict(list)      # wartosc -> [(run, task, model, quant)]
allvals=collections.Counter()
numvals=collections.Counter()
for tj in glob.glob("results/**/trajectories.jsonl", recursive=True):
    run=os.path.dirname(tj)
    sm=os.path.join(run,"summary.json")
    md=json.load(open(sm,encoding="utf-8")) if os.path.exists(sm) else {}
    model,quant=md.get("model_id","?"),md.get("quant","?")
    for l in open(tj,encoding="utf-8"):
        t=json.loads(l)
        for s in t["steps"]:
            for o in json_objects(s["raw_model_output"]):
                if isinstance(o,dict) and o.get("action")=="final_answer" and "answer" in o:
                    a=o["answer"]
                    if isinstance(a,(int,float)) and not isinstance(a,bool):
                        numvals[a]+=1
                        if abs(a-59)<1e-9: hits[59].append((run,t["task_id"],model,quant))
print("=== NAJCZESTSZE LICZBOWE final_answer w CALYM zbiorze (wszystkie runy) ===")
print(f"{'wartosc':>10}{'wystapien':>11}   F->C  (czy to okragla konwersja?)")
print("-"*62)
for v,n in numvals.most_common(15):
    c=(v-32)*5/9
    mark="  <-- F(%g C) DOKLADNIE" % c if abs(c-round(c*2)/2)<1e-9 else ""
    print(f"{v:>10}{n:>11}   {c:6.2f}{mark}")
print(f"\n  roznych wartosci liczbowych: {len(numvals)}   lacznie wystapien: {sum(numvals.values())}")
print()
print(f"=== WSZYSTKIE wystapienia final_answer == 59 : {len(hits[59])} ===")
g=collections.Counter((m,q,os.path.basename(os.path.dirname(r)),os.path.basename(r)) for r,t,m,q in hits[59])
for (m,q,parent,run),n in sorted(g.items()):
    tasks=sorted({t for r,t,mm,qq in hits[59] if mm==m and qq==q and os.path.basename(r)==run})
    print(f"  {m:<22}{q:<8}{parent}/{run:<22} n={n:<4} zadania={tasks}")
