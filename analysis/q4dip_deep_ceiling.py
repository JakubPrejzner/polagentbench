# -*- coding: utf-8 -*-
"""
Dip Q4: sufit hojny wewnatrz kubelka glebokosci 4+.

CO LICZY:
Zawezenie analizy A/B/C do 25 zadan o lancuchu co najmniej 4 wywolan, czyli tam gdzie dip
faktycznie zyje. Odpowiada na pytanie, czy dip przezywa darowanie kaskad NA TEJ GLEBOKOSCI.
Przezywa: -0.320 wobec Q5 po darowaniu A+B, przy czym Q5 osiaga wtedy 25/25, a Q4 17/25.

CZYTA Z:
  jak w q4dip_classify.py

PRODUKUJE:
  Sesja 3, Analiza 1: TABELA 1d.

TYLKO ODCZYT - skrypt niczego nie zapisuje ani nie modyfikuje.
Uruchamiac z katalogu glownego repo:
  .venv/Scripts/python.exe analysis/q4dip_deep_ceiling.py
"""
import json,sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
sys.path.insert(0,"src")
from polagentbench.io import load_all_tasks
from polagentbench.types import Trajectory
from polagentbench.eval.smoke import evaluate, SmokeStatus
BASE="results/v3_11b_2026-06-18"
TASKS={t.id:t for t in load_all_tasks(Path("tasks/adversarial"))}
FORMAT={"unknown_action","no_json_found","invalid_json","schema_violation","final_answer_shape_violation","final_answer_missing"}
CONTENT={"wrong_final_answer","wrong_tool_order","expected_tool_not_called","unexpected_tool_call",
         "unauthorized_side_effect","hallucinated_tool_result","tool_call_failed","timeout","loop"}
def chain(t):
    sp=t.expected_final_state or {}
    for k in ("tools_called_in_order_strict","tools_called_in_order","ordered_tools","tools_called_in_order_loose"):
        if k in sp: return [(c["tool"] if isinstance(c,dict) else str(c)) for c in sp[k]]
    return [] if "no_tool_calls" in sp else None
DEEP=[i for i in TASKS if (chain(TASKS[i]) is not None and len(chain(TASKS[i]))>=4)]
print(f"zadan o glebokosci >=4: {len(DEEP)}")
print()
print(f"{'kwant':<9}{'PASS':>8}{'A':>5}{'B':>5}{'C':>5}{'sufit ostrozny':>17}{'sufit hojny':>16}")
print("-"*65)
V={}
for q,d in [("Q3_K_M","q3_no_repair"),("Q4_K_M","q4_no_repair"),("Q5_K_M","q5_no_repair")]:
    A=B=C=P=0
    for line in open(f"{BASE}/{d}/trajectories.jsonl",encoding="utf-8"):
        tr=Trajectory.model_validate(json.loads(line))
        if tr.task_id not in DEEP: continue
        sr=evaluate(TASKS[tr.task_id],tr)
        if sr.status is SmokeStatus.PASS: P+=1; continue
        tg=set(sr.failure_tags)|{x.value.lower() for x in tr.failure_tags}
        f,c=tg&FORMAT,tg&CONTENT
        if c and not f: C+=1
        elif c and f: B+=1
        else: A+=1
    n=len(DEEP); V[q]=(P,A,B,C,n)
    print(f"{q:<9}{f'{P}/{n}':>8}{A:>5}{B:>5}{C:>5}"
          f"{f'{P+A}/{n} = {(P+A)/n:.3f}':>17}{f'{P+A+B}/{n} = {(P+A+B)/n:.3f}':>16}")
print()
for lbl,fn in (("scisle",lambda v:v[0]),("po A",lambda v:v[0]+v[1]),("po A+B",lambda v:v[0]+v[1]+v[2])):
    n=V["Q4_K_M"][4]
    q3,q4,q5=fn(V["Q3_K_M"])/n,fn(V["Q4_K_M"])/n,fn(V["Q5_K_M"])/n
    print(f"  glebokosc 4+, {lbl:<7} Q3={q3:.3f}  Q4={q4:.3f}  Q5={q5:.3f}   dip Q4-Q5={q4-q5:+.3f}  Q4-Q3={q4-q3:+.3f}")
