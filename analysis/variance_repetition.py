# -*- coding: utf-8 -*-
"""
Wariancja: test hipotezy o zaklinowanym samplerze i porownanie zadan miedzy seedami.

CO LICZY:
Liczy powtarzalnosc wyjsc w obrebie trajektorii, czyli sygnature zapetlenia. Hipoteza sie NIE
broni: najwiecej powtorzen ma seed3 (13.7 procent), ktory punktuje najlepiej. Drugi blok
wybiera zadania PASS w seed2 i seed3 przy FAIL w seed1 i pokazuje krok po kroku, co seed1
zrobil inaczej - ta sama tresc odpowiedzi, tylko jeden nadmiarowy krok bez JSON-a albo nazwa
narzedzia wpisana rowniez w pole action.

CZYTA Z:
  results/v3_11b_variance_2026-07-29/*/{run.log,trajectories.jsonl}

PRODUKUJE:
  Sesja 2, Analiza 2: TABELA 2d oraz cytaty w sekcji 2c.

TYLKO ODCZYT - skrypt niczego nie zapisuje ani nie modyfikuje.
Uruchamiac z katalogu glownego repo:
  .venv/Scripts/python.exe analysis/variance_repetition.py
"""
import json, re, sys, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE="results/v3_11b_variance_2026-07-29"

def load(r):
    return [json.loads(l) for l in open(f"{BASE}/{r}/trajectories.jsonl",encoding="utf-8")]
def verd(r):
    v={}
    for ln in open(f"{BASE}/{r}/run.log",encoding="utf-8"):
        m=re.match(r"^(\S+)\s+([✓✗?])\s+(.*)$",ln.rstrip("\n"))
        if m:
            tail=m.group(3); tg=[]
            if " - " in tail: tg=[t.strip() for t in tail.rsplit(" - ",1)[1].split(",")]
            v[m.group(1)]=("PASS" if m.group(2)=="✓" else "FAIL",tg)
    return v

print("="*96)
print("D. POWTARZALNOSC WYJSC W OBREBIE TRAJEKTORII (sygnatura zaklinowanego samplera)")
print("="*96)
print(f"{'run':<10}{'traj z powtorzonym':>22}{'max powtorzen':>16}{'krokow bedacych':>18}{'udzial':>10}")
print(f"{'':<10}{'wyjsciem (>=2 te same)':>22}{'tego samego':>16}{'powtorka':>18}{'':>10}")
print("-"*96)
for r in ["q8_seed1","q8_seed2","q8_seed3","q3_seed1","q3_seed2","q3_seed3"]:
    tr=load(r); nrep=0; mx=0; dup=0; tot=0
    for t in tr:
        outs=[s["raw_model_output"] for s in t["steps"]]
        tot+=len(outs)
        c=collections.Counter(outs)
        if outs and c.most_common(1)[0][1]>=2: nrep+=1
        if outs: mx=max(mx,c.most_common(1)[0][1])
        dup+=len(outs)-len(set(outs))
    print(f"{r:<10}{nrep:>22}{mx:>16}{dup:>18}{dup/tot:>9.1%}")

print()
print("="*96)
print("E. TE SAME ZADANIA: PASS w seed2 i seed3, FAIL w seed1 (Q8) — co seed1 zrobil inaczej")
print("="*96)
v1,v2,v3 = verd("q8_seed1"),verd("q8_seed2"),verd("q8_seed3")
t1 = {t["task_id"]:t for t in load("q8_seed1")}
t2 = {t["task_id"]:t for t in load("q8_seed2")}
flip=[k for k in v1 if v1[k][0]=="FAIL" and v2.get(k,("",))[0]=="PASS" and v3.get(k,("",))[0]=="PASS"]
print(f"zadan PASS/PASS w seed2+3 a FAIL w seed1: {len(flip)} z 67")
tagc=collections.Counter(tg for k in flip for tg in v1[k][1])
print(f"tagi seed1 na tych zadaniach: {dict(tagc.most_common())}")
print()
for k in flip[:3]:
    a,b = t1[k], t2[k]
    print(f"---- {k}   seed1: {len(a['steps'])} krokow / FAIL [{', '.join(v1[k][1])}]   |   seed2: {len(b['steps'])} krokow / PASS")
    print(f"     SEED 1:")
    for s in a["steps"][:6]:
        pe=s["parse_error"]; tag=f"parse_error[{pe['category']}]" if pe else (s['parsed_action'] or {}).get('action')
        print(f"        k{s['step_idx']} [{tag}] {s['raw_model_output'][:140].replace(chr(10),' ')}")
    if len(a["steps"])>6: print(f"        … (+{len(a['steps'])-6} krokow)")
    print(f"     SEED 2:")
    for s in b["steps"][:6]:
        pe=s["parse_error"]; tag=f"parse_error[{pe['category']}]" if pe else (s['parsed_action'] or {}).get('action')
        print(f"        k{s['step_idx']} [{tag}] {s['raw_model_output'][:140].replace(chr(10),' ')}")
    print()
