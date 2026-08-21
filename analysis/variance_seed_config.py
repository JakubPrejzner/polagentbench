# -*- coding: utf-8 -*-
"""
Wariancja: czy seed trafil do konfiguracji i czy run seed1 wystartowal.

CO LICZY:
Zestawia summary.json, gdzie seed i temperature sa None, z polami seed i temperature
w rekordach trajektorii - te maja poprawne 1/2/3 przy T=0.7, wiec przypisanie runu do seeda
po nazwie katalogu jest potwierdzone niezaleznie danymi. Dalej mierzy ksztalt runu seed1:
liczbe trajektorii, trajektorie zerokrokowe, puste wyjscia, mediane dlugosci, tokeny, czas.
Wynik: seed1 wyprodukowal WIECEJ tekstu i pracowal DLUZEJ niz seed2, ktory punktuje 6x lepiej.

CZYTA Z:
  results/v3_11b_variance_2026-07-29/{q8,q3}_seed{1,2,3}/{summary.json,trajectories.jsonl}

PRODUKUJE:
  Sesja 2, Analiza 2: TABELA 2a i TABELA 2b.

TYLKO ODCZYT - skrypt niczego nie zapisuje ani nie modyfikuje.
Uruchamiac z katalogu glownego repo:
  .venv/Scripts/python.exe analysis/variance_seed_config.py
"""
import json, re, sys, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "results/v3_11b_variance_2026-07-29"
RUNS = ["q8_seed1","q8_seed2","q8_seed3","q3_seed1","q3_seed2","q3_seed3"]

print("=" * 104)
print("A. CZY SEED I TEMPERATURA W OGOLE TRAFILY DO KONFIGURACJI (pola z trajectories.jsonl, nie z summary.json)")
print("=" * 104)
print(f"{'katalog':<12}{'summary.seed':>14}{'summary.temp':>14}{'seed w traj.':>16}{'temp w traj.':>16}{'passed':>10}")
print("-" * 104)
for r in RUNS:
    sm = json.load(open(f"{BASE}/{r}/summary.json", encoding="utf-8"))
    tr = [json.loads(l) for l in open(f"{BASE}/{r}/trajectories.jsonl", encoding="utf-8")]
    seeds = sorted({t["seed"] for t in tr}); temps = sorted({t["temperature"] for t in tr})
    print(f"{r:<12}{str(sm.get('seed')):>14}{str(sm.get('temperature')):>14}"
          f"{str(seeds):>16}{str(temps):>16}{str(sm['num_passed'])+'/'+str(sm['num_total']):>10}")

print()
print("=" * 104)
print("B. CZY RUN SEED1 W OGOLE WYSTARTOWAL — ksztalt trajektorii Q8")
print("=" * 104)
print(f"{'':<14}{'seed1':>14}{'seed2':>14}{'seed3':>14}")
print("-" * 60)
D = {}
for r in ["q8_seed1","q8_seed2","q8_seed3"]:
    tr = [json.loads(l) for l in open(f"{BASE}/{r}/trajectories.jsonl", encoding="utf-8")]
    steps = [s for t in tr for s in t["steps"]]
    D[r] = dict(
        ntraj=len(tr),
        nsteps=len(steps),
        spt=len(steps)/len(tr),
        zero_step=sum(1 for t in tr if not t["steps"]),
        empty_out=sum(1 for s in steps if not s["raw_model_output"].strip()),
        toolcalls=sum(1 for s in steps if (s["parsed_action"] or {}).get("action")=="call_tool"),
        finalans=sum(1 for s in steps if (s["parsed_action"] or {}).get("action")=="final_answer"),
        parse_ok=sum(1 for s in steps if not s["parse_error"]),
        tokens=sum(t["total_tokens"] for t in tr),
        lat=sum(t["total_latency_ms"] for t in tr)/1000,
        maxstep=sum(1 for t in tr if len(t["steps"])>=8),
        medlen=sorted(len(s["raw_model_output"]) for s in steps)[len(steps)//2],
    )
def row(lbl, k, fmt=str):
    print(f"{lbl:<14}" + "".join(f"{fmt(D[r][k]):>14}" for r in ["q8_seed1","q8_seed2","q8_seed3"]))
row("trajektorii","ntraj"); row("krokow","nsteps"); row("krokow/traj","spt",lambda v:f"{v:.2f}")
row("0-krokowych","zero_step"); row("pustych wyjsc","empty_out")
row("call_tool","toolcalls"); row("final_answer","finalans")
row("parse OK","parse_ok"); row("=max_steps(8)","maxstep")
row("mediana zn.","medlen"); row("tokenow","tokens"); row("czas [s]","lat",lambda v:f"{v:.0f}")

print()
print("=" * 104)
print("C. ROZKLAD KATEGORII BLEDOW PARSOWANIA — Q8")
print("=" * 104)
for r in ["q8_seed1","q8_seed2","q8_seed3"]:
    tr = [json.loads(l) for l in open(f"{BASE}/{r}/trajectories.jsonl", encoding="utf-8")]
    c = collections.Counter(s["parse_error"]["category"] for t in tr for s in t["steps"] if s["parse_error"])
    sm = json.load(open(f"{BASE}/{r}/summary.json", encoding="utf-8"))
    print(f"  {r}: {dict(c)}")
    print(f"      summary.failure_tag_counts = {sm['failure_tag_counts']}")
