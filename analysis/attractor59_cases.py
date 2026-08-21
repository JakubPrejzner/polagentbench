# -*- coding: utf-8 -*-
"""
Atraktor 59: cztery zadania L1 z odpowiedzia 59, pelny material dowodowy.

CO LICZY:
Dla v3_ext_L1_{a,e,h,i} wypisuje pelny prompt, ograniczenia, golden, cala trajektorie krok po
kroku wraz z wynikami narzedzi, oraz sprawdza, czy liczba 59 wystepuje gdziekolwiek w wejsciu
(prompt / ograniczenia / wynik narzedzia). Pokazuje, ze model wykonuje poprawny lancuch,
dostaje z narzedzia wartosci o sredniej rownej goldenowi i mimo to odpowiada 59, powtarzajac
te odpowiedz az do max_steps.

CZYTA Z:
  results/v3_11b_ladder_2026-07-29/q8_no_repair/trajectories.jsonl, tasks/ladder_ext/*.yaml

PRODUKUJE:
  Sesja 3, Analiza 2: TABELA 2a.

TYLKO ODCZYT - skrypt niczego nie zapisuje ani nie modyfikuje.
Uruchamiac z katalogu glownego repo:
  .venv/Scripts/python.exe analysis/attractor59_cases.py
"""
import json, sys, glob, yaml, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RUN="results/v3_11b_ladder_2026-07-29/q8_no_repair"
TARGET=["v3_ext_L1_a","v3_ext_L1_e","v3_ext_L1_h","v3_ext_L1_i"]
Y={}
for f in glob.glob("tasks/ladder_ext/v3_ext_*.yaml"):
    d=yaml.safe_load(open(f,encoding="utf-8")); Y[d["id"]]=d
T={json.loads(l)["task_id"]:json.loads(l) for l in open(f"{RUN}/trajectories.jsonl",encoding="utf-8")}

def find59(s):
    """Gdzie w tekscie wystepuje 59 jako liczba (nie fragment innej)."""
    return [m.start() for m in re.finditer(r"(?<![0-9.,])59(?![0-9])", s)]

for tid in TARGET:
    y=Y[tid]; t=T[tid]
    print("="*104)
    print(f"### {tid}    golden = {y['expected_final_state']['final_answer_contains_any']}")
    print("="*104)
    print("PROMPT:")
    print(f"   {y['prompt']}")
    print(f"   ograniczenia: {y.get('constraints')}")
    print()
    print("TRAJEKTORIA:")
    for s in t["steps"]:
        pa=s["parsed_action"] or {}; pe=s["parse_error"]
        tag=f"parse_error[{pe['category']}]" if pe else pa.get("action")
        line=f"   k{s['step_idx']} [{tag}]"
        if pa.get("action")=="call_tool":
            line+=f" {pa.get('tool')}({json.dumps(pa.get('arguments'),ensure_ascii=False)})"
        print(line)
        if s["tool_result"] is not None:
            print(f"        -> WYNIK: {json.dumps(s['tool_result'],ensure_ascii=False)}")
        if pe or pa.get("action")=="final_answer":
            print(f"        surowe: {s['raw_model_output'][:200]}")
    print()
    # gdzie wystepuje 59
    print("GDZIE WYSTEPUJE '59' W WEJSCIU:")
    hits=False
    if find59(y["prompt"]): print(f"   PROMPT: TAK, pozycje {find59(y['prompt'])}"); hits=True
    for c in (y.get("constraints") or []):
        if find59(c): print(f"   OGRANICZENIE: TAK -> {c}"); hits=True
    for s in t["steps"]:
        if s["tool_result"] is not None:
            js=json.dumps(s["tool_result"],ensure_ascii=False)
            if find59(js): print(f"   WYNIK NARZEDZIA k{s['step_idx']}: TAK -> {js}"); hits=True
    if not hits: print("   NIGDZIE — ani w promptcie, ani w ograniczeniach, ani w zadnym wyniku narzedzia")
    print()
