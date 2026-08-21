# -*- coding: utf-8 -*-
"""
Dip Q4 na Bielik-11B: klasyfikacja porazek A/B/C i sufity.

CO LICZY:
Odtwarza werdykty oracle kodem repo (eval.smoke.evaluate), bo katalog czerwcowy nie ma run.log.
Waliduje odtworzenie wobec summary.json oraz analysis/per_task_matrix.csv i wymaga zera
rozjazdow. Klasyfikuje porazki na A (czysty format), B (format + tresc, kaskada mozliwa),
C (czysta tresc). Liczy sufit ostrozny (darowane A) i hojny (darowane A+B) dla Q3/Q4/Q5.
Wynik: dip kurczy sie z -0.209 do -0.090 wobec Q5, ale nie znika.

CZYTA Z:
  results/v3_11b_2026-06-18/{q3,q4,q5}_no_repair/{trajectories.jsonl,summary.json},
  results/v3_11b_2026-06-18/analysis/per_task_matrix.csv,
  tasks/adversarial/*.yaml, src/polagentbench/ (eval.smoke.evaluate)

PRODUKUJE:
  Sesja 3, Analiza 1: TABELA 1a i TABELA 1b.

TYLKO ODCZYT - skrypt niczego nie zapisuje ani nie modyfikuje.
Uruchamiac z katalogu glownego repo:
  .venv/Scripts/python.exe analysis/q4dip_classify.py
"""
import json, sys, csv, glob, collections
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, "src")
from polagentbench.io import load_all_tasks
from polagentbench.types import Trajectory
from polagentbench.eval.smoke import evaluate, SmokeStatus

BASE = "results/v3_11b_2026-06-18"
QUANTS = [("Q3_K_M","q3_no_repair"), ("Q4_K_M","q4_no_repair"), ("Q5_K_M","q5_no_repair")]
TASKS = {t.id: t for t in load_all_tasks(Path("tasks/adversarial"))}
print(f"zadan zaladowanych: {len(TASKS)}")

FORMAT  = {"unknown_action","no_json_found","invalid_json","schema_violation",
           "final_answer_shape_violation","final_answer_missing"}
CONTENT = {"wrong_final_answer","wrong_tool_order","expected_tool_not_called",
           "unexpected_tool_call","unauthorized_side_effect","hallucinated_tool_result",
           "tool_call_failed","timeout","loop"}

R = {}
for q, d in QUANTS:
    res = {}
    for line in open(f"{BASE}/{d}/trajectories.jsonl", encoding="utf-8"):
        tr = Trajectory.model_validate(json.loads(line))
        sr = evaluate(TASKS[tr.task_id], tr)
        tags = set(sr.failure_tags) | {t.value.lower() for t in tr.failure_tags}
        res[tr.task_id] = (sr.status, tags, tr)
    R[q] = res

print()
print("=== WALIDACJA odtworzonego oracle wobec summary.json i per_task_matrix.csv ===")
mat = {r["task_id"]: r for r in csv.DictReader(open(f"{BASE}/analysis/per_task_matrix.csv", encoding="utf-8"))}
col = {"Q3_K_M":"q3_no_repair","Q4_K_M":"q4_no_repair","Q5_K_M":"q5_no_repair"}
for q, d in QUANTS:
    sm = json.load(open(f"{BASE}/{d}/summary.json", encoding="utf-8"))
    mine = sum(1 for s,_,_ in R[q].values() if s is SmokeStatus.PASS)
    dis = [t for t in R[q] if (R[q][t][0] is SmokeStatus.PASS) != (mat[t][col[q]] == "PASS")]
    print(f"  {q}: odtworzone PASS={mine}  summary.num_passed={sm['num_passed']}  "
          f"{'ZGODNE' if mine==sm['num_passed'] else 'ROZJAZD'}   niezgodnych z macierza: {len(dis)} {dis if dis else ''}")

print()
print("=== TABELA 1a — klasyfikacja porazek A/B/C i sufit hojny ===")
print(f"{'kwant':<9}{'PASS':>8}{'porazek':>9}{'A format':>10}{'B kaskada':>11}{'C tresc':>9}"
      f"{'sufit ostrozny':>17}{'sufit hojny':>16}")
print("-"*89)
CEIL = {}
for q,_ in QUANTS:
    A=B=C=0
    for tid,(st,tg,_) in R[q].items():
        if st is SmokeStatus.PASS: continue
        f,c = tg&FORMAT, tg&CONTENT
        if c and not f: C+=1
        elif c and f:   B+=1
        else:           A+=1
    p = 67-(A+B+C)
    CEIL[q]=(p,A,B,C)
    print(f"{q:<9}{str(p)+'/67':>8}{A+B+C:>9}{A:>10}{B:>11}{C:>9}"
          f"{f'{p+A}/67 = {(p+A)/67:.3f}':>17}{f'{p+A+B}/67 = {(p+A+B)/67:.3f}':>16}")

print()
print("=== PYTANIE ROZSTRZYGAJACE: czy dip Q4 przezywa darowanie kaskad? ===")
for lbl, idx in (("scisle", 0), ("po darowaniu A", 1), ("po darowaniu A+B", 2)):
    def val(q):
        p,A,B,C = CEIL[q]
        return p if idx==0 else (p+A if idx==1 else p+A+B)
    q3,q4,q5 = val("Q3_K_M"), val("Q4_K_M"), val("Q5_K_M")
    print(f"  {lbl:<18} Q3={q3}/67 ({q3/67:.3f})   Q4={q4}/67 ({q4/67:.3f})   Q5={q5}/67 ({q5/67:.3f})   "
          f"dip Q4 vs Q5 = {(q4-q5)/67:+.3f}   vs Q3 = {(q4-q3)/67:+.3f}")
