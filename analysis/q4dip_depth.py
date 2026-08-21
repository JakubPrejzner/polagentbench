# -*- coding: utf-8 -*-
"""
Dip Q4: stratyfikacja wg glebokosci lancucha oraz zuzycie krokow.

CO LICZY:
Grupuje 67 zadan wg dlugosci oczekiwanego lancucha (0-1 / 2-3 / 4+ / brak checku) i liczy
pass rate osobno w kazdym kubelku dla Q3/Q4/Q5. To ten skrypt pokazuje, ze caly dip siedzi
w kubelku 4+ (0.32 wobec 0.84 na Q5), a przy 2-3 wywolaniach Q4 jest WYZEJ niz Q5 i Q3.
Dodatkowo mierzy zuzycie krokow (krokow na trajektorie, trajektorie na max_steps, timeouty)
oraz mechanizm w kubelku 4+ (udane call_tool wobec unknown_action).

CZYTA Z:
  jak w q4dip_classify.py

PRODUKUJE:
  Sesja 3, Analiza 1: TABELA 1c i TABELA 1e.

TYLKO ODCZYT - skrypt niczego nie zapisuje ani nie modyfikuje.
Uruchamiac z katalogu glownego repo:
  .venv/Scripts/python.exe analysis/q4dip_depth.py
"""
import json, sys, collections
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0,"src")
from polagentbench.io import load_all_tasks
from polagentbench.types import Trajectory
from polagentbench.eval.smoke import evaluate, SmokeStatus
BASE="results/v3_11b_2026-06-18"
TASKS={t.id:t for t in load_all_tasks(Path("tasks/adversarial"))}
def chain(t):
    sp=t.expected_final_state or {}
    for k in ("tools_called_in_order_strict","tools_called_in_order","ordered_tools","tools_called_in_order_loose"):
        if k in sp: return [(c["tool"] if isinstance(c,dict) else str(c)) for c in sp[k]]
    if "no_tool_calls" in sp: return []
    return None
DEPTH={i:(len(chain(TASKS[i])) if chain(TASKS[i]) is not None else None) for i in TASKS}
Q=[("Q3_K_M","q3_no_repair"),("Q4_K_M","q4_no_repair"),("Q5_K_M","q5_no_repair")]
R={}
for q,d in Q:
    res={}
    for line in open(f"{BASE}/{d}/trajectories.jsonl",encoding="utf-8"):
        raw=json.loads(line)
        tr=Trajectory.model_validate(raw)
        sr=evaluate(TASKS[tr.task_id],tr)
        res[tr.task_id]=(sr.status is SmokeStatus.PASS, raw)
    R[q]=res
def rate(q,ids): return sum(1 for i in ids if R[q][i][0])/len(ids)
def cnt(q,ids):  return sum(1 for i in ids if R[q][i][0])

buckets=[("0-1 wywolan",lambda d:d is not None and d<=1),
         ("2-3 wywolania",lambda d:d is not None and 2<=d<=3),
         ("4+ wywolan",  lambda d:d is not None and d>=4),
         ("brak checku", lambda d:d is None)]
print("=== TABELA 1c — pass rate wg GLEBOKOSCI oczekiwanego lancucha (main 67, repair off) ===")
print(f"{'glebokosc':<16}{'n':>4}" + "".join(f"{q:>16}" for q,_ in Q) + f"{'Q4-Q5':>9}{'Q4-Q3':>9}")
print("-"*90)
for lbl,f in buckets:
    ids=[i for i in TASKS if f(DEPTH[i])]
    if not ids: continue
    cells="".join(f"{str(cnt(q,ids))+'/'+str(len(ids))+' ('+format(rate(q,ids),'.2f')+')':>16}" for q,_ in Q)
    d5=rate("Q4_K_M",ids)-rate("Q5_K_M",ids); d3=rate("Q4_K_M",ids)-rate("Q3_K_M",ids)
    print(f"{lbl:<16}{len(ids):>4}{cells}{format(d5,'+.2f'):>9}{format(d3,'+.2f'):>9}")

print()
print("=== TABELA 1d — zuzycie krokow, cala suita ===")
print(f"{'kwant':<9}{'krokow':>9}{'krokow/traj':>13}{'traj. na max_steps':>20}{'traj. z timeout':>17}")
print("-"*68)
for q,d in Q:
    raws=[r for _,r in R[q].values()]
    st=sum(len(r["steps"]) for r in raws)
    mx=sum(1 for r in raws if len(r["steps"])>=TASKS[r["task_id"]].max_steps)
    to=sum(1 for r in raws if any(str(x).lower().endswith("timeout") for x in r["failure_tags"]))
    print(f"{q:<9}{st:>9}{st/len(raws):>13.2f}{mx:>20}{to:>17}")

print()
print("=== TABELA 1e — tylko zadania o glebokosci 4+ : co robi Q4 ===")
ids=[i for i in TASKS if DEPTH[i] is not None and DEPTH[i]>=4]
print(f"{'kwant':<9}{'PASS':>8}{'sr. krokow':>12}{'na max_steps':>14}{'udanych call_tool':>19}{'unknown_action':>16}{'no_json':>9}")
print("-"*88)
for q,d in Q:
    raws=[R[q][i][1] for i in ids]
    p=cnt(q,ids)
    stp=sum(len(r["steps"]) for r in raws)/len(raws)
    mx=sum(1 for r in raws if len(r["steps"])>=TASKS[r["task_id"]].max_steps)
    ct=sum(1 for r in raws for s in r["steps"] if (s["parsed_action"] or {}).get("action")=="call_tool")
    ua=sum(1 for r in raws for s in r["steps"] if s["parse_error"] and s["parse_error"]["category"]=="unknown_action")
    nj=sum(1 for r in raws for s in r["steps"] if s["parse_error"] and s["parse_error"]["category"]=="no_json_found")
    print(f"{q:<9}{str(p)+'/'+str(len(ids)):>8}{stp:>12.2f}{mx:>14}{ct:>19}{ua:>16}{nj:>9}")
