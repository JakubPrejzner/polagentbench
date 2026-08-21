# -*- coding: utf-8 -*-
"""
PLLuM: surowe raw_model_output pierwszych 10 failujacych trajektorii.

CO LICZY:
Czyta werdykty oracle z run.log, wybiera pierwsze 10 porazek i wypisuje kazdy krok: kategorie
parse_error albo sparsowana akcje, dlugosc i tresc surowego wyjscia. Material pod pytanie
'czy model w ogole mowi naszym protokolem' - widac poprawne koperty call_tool obok
splaszczonych, halucynowane wyniki narzedzi oraz rozmowe modelu z samym soba (adv_010).

CZYTA Z:
  results/v3_pllum_2026-07-29/q8_main_no_repair/{run.log,trajectories.jsonl}

PRODUKUJE:
  Sesja 2, Analiza 1: sekcja 1b (cytaty surowych wyjsc).

TYLKO ODCZYT - skrypt niczego nie zapisuje ani nie modyfikuje.
Uruchamiac z katalogu glownego repo:
  .venv/Scripts/python.exe analysis/pllum_raw_dump.py
"""
import json, re, sys, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RUN = "results/v3_pllum_2026-07-29/q8_main_no_repair"

# werdykty oracle z run.log
verdict = {}
for ln in open(f"{RUN}/run.log", encoding="utf-8"):
    m = re.match(r"^(\S+)\s+([✓✗?])\s", ln)
    if m: verdict[m.group(1)] = m.group(2)
print(f"werdyktow z run.log: {len(verdict)}  PASS={sum(1 for v in verdict.values() if v=='✓')}  FAIL={sum(1 for v in verdict.values() if v=='✗')}")

trajs = [json.loads(l) for l in open(f"{RUN}/trajectories.jsonl", encoding="utf-8")]
fails = [t for t in trajs if verdict.get(t["task_id"]) == "✗"]
print(f"trajektorii: {len(trajs)}  failujacych: {len(fails)}")
print()
print("=" * 100)
print("PIERWSZE 10 FAILUJACYCH TRAJEKTORII — raw_model_output krok po kroku")
print("=" * 100)
for t in fails[:10]:
    print(f"\n#### {t['task_id']}   krokow={len(t['steps'])}  total_tokens={t['total_tokens']}  temp={t['temperature']} seed={t['seed']}")
    for s in t["steps"]:
        raw = s["raw_model_output"]
        pe = s["parse_error"]
        pa = s["parsed_action"]
        tag = f"parse_error[{pe['category']}]" if pe else (f"OK->{ (pa or {}).get('action') }" if pa else "brak")
        print(f"  krok {s['step_idx']}  [{tag}]  len={len(raw)}")
        body = raw if len(raw) <= 400 else raw[:400] + f" …(+{len(raw)-400} zn.)"
        for line in body.splitlines() or [""]:
            print(f"      | {line}")
