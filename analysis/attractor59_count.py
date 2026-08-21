# -*- coding: utf-8 -*-
"""
Atraktor 59: uczciwe zliczanie na poziomie par (run, zadanie).

CO LICZY:
Naprawia zawyzenie z attractor59_scan_raw.py: deduplikuje odpowiedzi w obrebie trajektorii
i liczy unikalne pary (run, zadanie). Pokazuje tez, skad bralo sie zawyzenie, wypisujac trzy
surowe wyjscia z powtorzonym obiektem. Wynik: 59.0 to najczestsza liczbowa odpowiedz w calym
zbiorze - 91 par, 26 zadan, 23 runy, oba modele, piec poziomow kwantyzacji.

CZYTA Z:
  results/**/trajectories.jsonl, results/**/summary.json

PRODUKUJE:
  Sesja 3, Analiza 2: TABELA 2b i TABELA 2c.

TYLKO ODCZYT - skrypt niczego nie zapisuje ani nie modyfikuje.
Uruchamiac z katalogu glownego repo:
  .venv/Scripts/python.exe analysis/attractor59_count.py
"""
import json, sys, glob, os, collections
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
print("=== skad bierze sie 61 — pokaz 3 surowe wyjscia ===")
n=0
for tj in glob.glob("results/**/trajectories.jsonl", recursive=True):
    for l in open(tj,encoding="utf-8"):
        t=json.loads(l)
        for s in t["steps"]:
            objs=[o for o in json_objects(s["raw_model_output"])
                  if isinstance(o,dict) and o.get("action")=="final_answer" and o.get("answer")==61]
            if objs and n<3:
                n+=1
                print(f"  {os.path.dirname(tj)} / {t['task_id']} / k{s['step_idx']}   obiektow z 61 w TYM kroku: {len(objs)}")
                print(f"    dlugosc wyjscia: {len(s['raw_model_output'])} zn.")
                print(f"    {s['raw_model_output'][:300]}")
    if n>=3: break

print()
print("=== ZLICZANIE UCZCIWE: unikalne pary (run, zadanie) z danym final_answer ===")
pairs=collections.defaultdict(set)
for tj in glob.glob("results/**/trajectories.jsonl", recursive=True):
    run=os.path.dirname(tj)
    for l in open(tj,encoding="utf-8"):
        t=json.loads(l)
        vals=set()
        for s in t["steps"]:
            for o in json_objects(s["raw_model_output"]):
                if isinstance(o,dict) and o.get("action")=="final_answer" and isinstance(o.get("answer"),(int,float)) and not isinstance(o.get("answer"),bool):
                    vals.add(o["answer"])
        for v in vals: pairs[v].add((run,t["task_id"]))
print(f"{'wartosc':>10}{'par (run,zadanie)':>19}{'roznych zadan':>15}{'roznych runow':>15}   F->C")
print("-"*80)
for v,st in sorted(pairs.items(), key=lambda kv:-len(kv[1]))[:12]:
    c=(v-32)*5/9
    mark="  <-- F(%g C)" % c if abs(c-round(c*2)/2)<1e-9 else ""
    print(f"{v:>10}{len(st):>19}{len({t for _,t in st}):>15}{len({r for r,_ in st}):>15}   {c:7.2f}{mark}")
print()
S=pairs[59]
print(f"=== 59: {len(S)} par (run, zadanie) ===")
print(f"  roznych zadan: {len({t for _,t in S})}")
print(f"  roznych runow: {len({r for r,_ in S})}")
mods=collections.Counter()
for r,t in S:
    sm=os.path.join(r,"summary.json")
    md=json.load(open(sm,encoding="utf-8")) if os.path.exists(sm) else {}
    mods[(md.get("model_id","?"), md.get("quant","?"))]+=1
print(f"  rozklad model/kwant: {dict(sorted(mods.items()))}")
print(f"  zadania: {sorted({t for _,t in S})}")
