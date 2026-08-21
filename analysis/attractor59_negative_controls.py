# -*- coding: utf-8 -*-
"""
Atraktor 59: kontrole negatywne.

CO LICZY:
Sprawdza cztery rzeczy: czy 59 jest goldenem jakiegokolwiek zadania (nie jest, 0 zadan),
czy 59 wystepuje w danych srodowiska (nie wystepuje ani razu), jakie temperatury w ogole zna
srodowisko (zakres -5.0 do 19.0, bez 15.0), oraz ile z 91 trajektorii ma 59 w promptcie
(zero) i ile w wyniku narzedzia (11 - te rozstrzyga attractor59_direction.py).

CZYTA Z:
  tasks/**/*.yaml, src/polagentbench/environments/weather.py, results/**/trajectories.jsonl

PRODUKUJE:
  Sesja 3, Analiza 2: TABELA 2d, wiersze 1-5.

TYLKO ODCZYT - skrypt niczego nie zapisuje ani nie modyfikuje.
Uruchamiac z katalogu glownego repo:
  .venv/Scripts/python.exe analysis/attractor59_negative_controls.py
"""
import json, sys, glob, yaml, re, os, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
G=collections.Counter(); allg={}
for f in glob.glob("tasks/**/*.yaml", recursive=True):
    try: d=yaml.safe_load(open(f,encoding="utf-8"))
    except Exception: continue
    if not isinstance(d,dict) or "expected_final_state" not in d: continue
    g=(d["expected_final_state"] or {}).get("final_answer_contains_any") or []
    allg[d.get("id",f)]=[str(x) for x in g]
    for x in g: G[str(x)]+=1
print("=== czy '59' wystepuje jako golden w JAKIMKOLWIEK zadaniu ===")
hit=[k for k,v in allg.items() if any(s.strip() in ("59","59.0","59,0") for s in v)]
print(f"  zadan z goldenem 59: {len(hit)}  {hit}")
print(f"  zadan z goldenem 61: {[k for k,v in allg.items() if any(s.strip() in ('61','61.0') for s in v)]}")
print(f"  zadan z goldenem 63: {[k for k,v in allg.items() if any(s.strip() in ('63','63.0') for s in v)]}")
print()
print("=== najczestsze goldeny w suicie (dla kontekstu) ===")
for v,n in G.most_common(10): print(f"   {v:>8}  w {n} zadaniach")
print()
print("=== jakie temperatury w ogole wystepuja w danych srodowiska ===")
src=open("src/polagentbench/environments/weather.py",encoding="utf-8").read()
temps=sorted({float(x) for x in re.findall(r"(?<![\w.])(-?\d{1,2}\.\d)(?![\w.])", src)})
print(f"   liczby zmiennoprzecinkowe w weather.py: {temps}")
print(f"   czy jest 15.0: {'TAK' if 15.0 in temps else 'NIE'}")
print(f"   czy jest 59 (jako liczba calkowita): {'TAK' if re.search(r'(?<![0-9.])59(?![0-9])', src) else 'NIE'}")
print()
print("=== czy 59 wystepuje w WEJSCIU ktoregokolwiek z 26 zadan, w ktorych padlo ===")
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
Y={}
for f in glob.glob("tasks/**/*.yaml", recursive=True):
    try: d=yaml.safe_load(open(f,encoding="utf-8"))
    except Exception: continue
    if isinstance(d,dict) and "id" in d: Y[d["id"]]=d
rx=re.compile(r"(?<![0-9.,])59(?![0-9])")
inprompt=intool=0; checked=set(); tot=0
for tj in glob.glob("results/**/trajectories.jsonl", recursive=True):
    for l in open(tj,encoding="utf-8"):
        t=json.loads(l)
        has59=any(isinstance(o,dict) and o.get("action")=="final_answer" and o.get("answer")==59
                  for s in t["steps"] for o in json_objects(s["raw_model_output"]))
        if not has59: continue
        tot+=1; checked.add(t["task_id"])
        y=Y.get(t["task_id"])
        if y and rx.search(y.get("prompt","")): inprompt+=1
        if any(s["tool_result"] is not None and rx.search(json.dumps(s["tool_result"],ensure_ascii=False)) for s in t["steps"]): intool+=1
print(f"   trajektorii z odpowiedzia 59: {tot}   roznych zadan: {len(checked)}")
print(f"   z nich majacych 59 w PROMPCIE:        {inprompt}")
print(f"   z nich majacych 59 w WYNIKU NARZEDZIA: {intool}")
