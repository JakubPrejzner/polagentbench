# -*- coding: utf-8 -*-
"""
Atraktor 59: kierunek przyczynowy w 11 przypadkach z 59 w wyniku narzedzia.

CO LICZY:
Dla kazdej trajektorii, ktora odpowiedziala 59 i miala 59 w wyniku narzedzia, wypisuje
argument podany narzedziu przez model. We wszystkich 11 przypadkach jest to
convert_temperature(value=15, celsius -> fahrenheit), czyli 59 nie przyszlo z kontekstu do
modelu, tylko model wymusil je na narzedziu. 15 C nie wystepuje w danych srodowiska,
wiec liczba 15 rowniez jest wymyslona.

CZYTA Z:
  results/**/trajectories.jsonl

PRODUKUJE:
  Sesja 3, Analiza 2: TABELA 2d, wiersz 6 (kierunek przyczynowy).

TYLKO ODCZYT - skrypt niczego nie zapisuje ani nie modyfikuje.
Uruchamiac z katalogu glownego repo:
  .venv/Scripts/python.exe analysis/attractor59_direction.py
"""
import json,sys,glob,os,re
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
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
rx=re.compile(r"(?<![0-9.,])59(?![0-9])")
found=0
print(f"{'run':<42}{'zadanie':<20}{'krok 59 w wyniku':>18}  argument, ktory model podal narzedziu")
print("-"*140)
for tj in sorted(glob.glob("results/**/trajectories.jsonl", recursive=True)):
    run=os.path.dirname(tj).replace("results"+os.sep,"")
    for l in open(tj,encoding="utf-8"):
        t=json.loads(l)
        has59=any(isinstance(o,dict) and o.get("action")=="final_answer" and o.get("answer")==59
                  for s in t["steps"] for o in json_objects(s["raw_model_output"]))
        if not has59: continue
        for s in t["steps"]:
            if s["tool_result"] is None: continue
            js=json.dumps(s["tool_result"],ensure_ascii=False)
            if not rx.search(js): continue
            found+=1
            pa=s["parsed_action"] or {}
            print(f"{run:<42}{t['task_id']:<20}{('k'+str(s['step_idx'])):>18}  "
                  f"{pa.get('tool')}({json.dumps(pa.get('arguments'),ensure_ascii=False)})")
            print(f"{'':<80}  -> wynik: {js[:90]}")
print(f"\n  znalezionych: {found}")
