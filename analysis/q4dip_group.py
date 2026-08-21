# -*- coding: utf-8 -*-
"""
Dip Q4: czy zadania padajace tylko na Q4 tworza spojna grupe.

CO LICZY:
Wybiera zadania PASS na Q5 i Q3 przy FAIL na Q4 (jest ich 14) i wypisuje dla kazdego rodzine,
oczekiwany lancuch narzedzi, klase A/B/C i tagi. Porownuje rozklady w grupie z rozkladami
w calej suicie: rodzina, dlugosc lancucha, pierwsze narzedzie, obecnosc convert_temperature.
Robi kontrole odwrotna - zadania PASS na Q4 przy FAIL na Q5 i Q3 (jest jedno, adv_004b).

CZYTA Z:
  jak w q4dip_classify.py

PRODUKUJE:
  Sesja 3, Analiza 1: TABELA 1f oraz tabela wzbogacen.

TYLKO ODCZYT - skrypt niczego nie zapisuje ani nie modyfikuje.
Uruchamiac z katalogu glownego repo:
  .venv/Scripts/python.exe analysis/q4dip_group.py
"""
import json, sys, collections, re
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0,"src")
from polagentbench.io import load_all_tasks
from polagentbench.types import Trajectory
from polagentbench.eval.smoke import evaluate, SmokeStatus

BASE="results/v3_11b_2026-06-18"
TASKS={t.id:t for t in load_all_tasks(Path("tasks/adversarial"))}
FORMAT={"unknown_action","no_json_found","invalid_json","schema_violation","final_answer_shape_violation","final_answer_missing"}
CONTENT={"wrong_final_answer","wrong_tool_order","expected_tool_not_called","unexpected_tool_call",
         "unauthorized_side_effect","hallucinated_tool_result","tool_call_failed","timeout","loop"}
R={}
for q,d in [("Q3_K_M","q3_no_repair"),("Q4_K_M","q4_no_repair"),("Q5_K_M","q5_no_repair")]:
    res={}
    for line in open(f"{BASE}/{d}/trajectories.jsonl",encoding="utf-8"):
        tr=Trajectory.model_validate(json.loads(line))
        sr=evaluate(TASKS[tr.task_id],tr)
        res[tr.task_id]=(sr.status is SmokeStatus.PASS, set(sr.failure_tags)|{t.value.lower() for t in tr.failure_tags}, tr)
    R[q]=res

def family(tid):
    if tid.startswith("v3_arith_"): return "v3_arith"
    if tid.startswith("v3_chain_"): return "v3_chain"
    if tid.startswith("adv_"):      return "adv"
    return "inne"
def expected_chain(t):
    sp=t.expected_final_state or {}
    for k in ("tools_called_in_order_strict","tools_called_in_order","ordered_tools","tools_called_in_order_loose"):
        if k in sp: return [(c["tool"] if isinstance(c,dict) else str(c)) for c in sp[k]]
    if "no_tool_calls" in sp: return []
    return None

ONLY_Q4 = sorted(t for t in TASKS if not R["Q4_K_M"][t][0] and R["Q5_K_M"][t][0] and R["Q3_K_M"][t][0])
print(f"=== TABELA 1b — zadania PASS na Q5 i Q3, FAIL na Q4: {len(ONLY_Q4)} z 67 ===")
print(f"{'task_id':<18}{'rodzina':<10}{'lancuch oczekiwany':<46}{'n':>3}{'klasa':>7}  tagi Q4")
print("-"*140)
for t in ONLY_Q4:
    ch=expected_chain(TASKS[t]); tg=R["Q4_K_M"][t][1]
    f,c=tg&FORMAT,tg&CONTENT
    kl = "C" if (c and not f) else ("B" if (c and f) else "A")
    chs = ">".join(ch) if ch is not None else "(brak checku lancucha)"
    print(f"{t:<18}{family(t):<10}{chs[:44]:<46}{(len(ch) if ch is not None else -1):>3}{kl:>7}  {sorted(tg)}")

print()
print("=== czy to spojna grupa? rozklady w grupie vs w calej suicie ===")
allids=sorted(TASKS)
def dist(ids, fn):
    c=collections.Counter(fn(i) for i in ids); n=len(ids)
    return ", ".join(f"{k}={v} ({v/n:.0%})" for k,v in sorted(c.items(), key=lambda kv:-kv[1]))
print(f"  rodzina    grupa: {dist(ONLY_Q4, family)}")
print(f"             suita: {dist(allids, family)}")
def nt(i):
    ch=expected_chain(TASKS[i]); return "brak checku" if ch is None else f"{len(ch)} wywolan"
print(f"  dlugosc    grupa: {dist(ONLY_Q4, nt)}")
print(f"             suita: {dist(allids, nt)}")
def firsttool(i):
    ch=expected_chain(TASKS[i]); return (ch[0] if ch else "-") if ch is not None else "brak checku"
print(f"  1. narzedzie grupa: {dist(ONLY_Q4, firsttool)}")
print(f"               suita: {dist(allids, firsttool)}")
def usesconv(i):
    ch=expected_chain(TASKS[i]); return "z convert" if (ch and "convert_temperature" in ch) else "bez convert"
print(f"  convert    grupa: {dist(ONLY_Q4, usesconv)}")
print(f"             suita: {dist(allids, usesconv)}")

print()
print("=== rozklad klas A/B/C w grupie ===")
kl=collections.Counter()
for t in ONLY_Q4:
    tg=R["Q4_K_M"][t][1]; f,c=tg&FORMAT,tg&CONTENT
    kl["C" if (c and not f) else ("B" if (c and f) else "A")]+=1
print(f"  {dict(kl)}   (A=czysty format, B=kaskada, C=czysta tresc)")
tagc=collections.Counter(x for t in ONLY_Q4 for x in R["Q4_K_M"][t][1])
print(f"  tagi w grupie: {dict(tagc.most_common())}")

print()
print("=== kontrola odwrotna: zadania FAIL na Q5 i Q3, a PASS na Q4 (czy Q4 ma cokolwiek swojego) ===")
INV=sorted(t for t in TASKS if R["Q4_K_M"][t][0] and not R["Q5_K_M"][t][0] and not R["Q3_K_M"][t][0])
print(f"  {len(INV)}: {INV}")
