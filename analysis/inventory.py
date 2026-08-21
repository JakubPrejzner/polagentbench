# -*- coding: utf-8 -*-
"""
Inwentarz wszystkich runow w results/.

CO LICZY:
Dla kazdego summary.json wypisuje model_id, kwant, suite (wywnioskowany z num_total), repair,
num_passed, liczbe splaszczonych kopert (parse_error unknown_action), liczbe krokow, obecnosc
run.log i commit. Sluzy do targetowania analiz - to on rozstrzygnal, ze jedynym runem main67
z dokladnie 18 splaszczonymi kopertami jest PLLuM-8B Q8, a nie zaden run Bielika-7B
(te maja 31 i 50).

CZYTA Z:
  results/**/summary.json, results/**/trajectories.jsonl

PRODUKUJE:
  Sesja 3: tabela inwentarza 120 runow (blok 'Inwentarz rozstrzyga targetowanie').

TYLKO ODCZYT - skrypt niczego nie zapisuje ani nie modyfikuje.
Uruchamiac z katalogu glownego repo:
  .venv/Scripts/python.exe analysis/inventory.py
"""
import json, glob, os, sys, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SUITE = {46:"ladder46", 67:"main67", 15:"easy15", 22:"main22", 5:"smoke5"}
rows=[]
for sm in glob.glob("results/**/summary.json", recursive=True):
    d=json.load(open(sm,encoding="utf-8"))
    run=os.path.dirname(sm)
    tj=os.path.join(run,"trajectories.jsonl")
    unk=nsteps=0
    if os.path.exists(tj):
        for l in open(tj,encoding="utf-8"):
            t=json.loads(l)
            for s in t["steps"]:
                nsteps+=1
                if s["parse_error"] and s["parse_error"]["category"]=="unknown_action": unk+=1
    rows.append((d.get("model_id",""), d.get("quant",""), SUITE.get(d.get("num_total"),str(d.get("num_total"))),
                 "ON" if d.get("repair") else "off", f"{d.get('num_passed')}/{d.get('num_total')}",
                 unk, nsteps, os.path.exists(os.path.join(run,"run.log")), d.get("git_ref",""), run))
rows.sort(key=lambda r:(r[0],r[2],r[1],r[3]))
print(f"{'model_id':<24}{'kwant':<8}{'suite':<10}{'rep':<5}{'wynik':>9}{'unknown_action':>16}{'krokow':>8}{'run.log':>9}{'commit':>9}  katalog")
print("-"*150)
for r in rows:
    print(f"{r[0]:<24}{r[1]:<8}{r[2]:<10}{r[3]:<5}{r[4]:>9}{r[5]:>16}{r[6]:>8}{('TAK' if r[7] else 'BRAK'):>9}{r[8]:>9}  {r[9]}")
print()
print("=== runy z DOKLADNIE 18 splaszczonymi kopertami (unknown_action) ===")
for r in rows:
    if r[5]==18: print(f"    {r[0]} {r[1]} {r[2]} repair={r[3]}  -> {r[9]}")
