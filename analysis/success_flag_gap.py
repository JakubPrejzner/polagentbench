# -*- coding: utf-8 -*-
"""
Flaga trajectory.success wobec oracle na 18 komorkach krzywej main67 (repair=off).

CO LICZY:
Dla kazdej z 18 komorek model x kwant suity main67 przy repair=off zestawia werdykt oracle
(num_passed z summary.json) z liczba trajektorii, ktore same o sobie mowia success=true
(pole success w trajectories.jsonl). Liczy roznice i sprawdza, w ilu komorkach flaga ZAWYZA
wynik. Wydruk uzasadnia zdanie z przypisu tabeli krzywej: flaga zawyza wynik we WSZYSTKICH
18 komorkach, a najgorzej u PLLuM-8B Q8_0 (flaga 66/67 wobec oracle 13/67).

Katalogi komorek sa te same, co w bootstrap_ci.py: 11B z v3_11b_2026-06-18, 7B z
v3_arith_clean_2026-06-18 (Q2/Q3/Q4/Q8) i v3_7b_grid_2026-07-29 (Q5/Q6), PLLuM
z v3_pllum_2026-07-29. Zgodnosc model_id z summary.json jest sprawdzana dla kazdej komorki.

CZYTA Z:
  results/v3_11b_2026-06-18/q{2,3,4,5,6,8}_no_repair/{summary.json,trajectories.jsonl}
  results/v3_arith_clean_2026-06-18/q{2,3,4,8}_no_repair/{summary.json,trajectories.jsonl}
  results/v3_7b_grid_2026-07-29/q{5,6}_no_repair/{summary.json,trajectories.jsonl}
  results/v3_pllum_2026-07-29/q{2,3,4,5,6,8}_main_no_repair/{summary.json,trajectories.jsonl}

PRODUKUJE:
  paper/tables/curve_main.tex (tab:curve_main): zdanie przypisu o fladze zawyzajacej wynik
  we wszystkich 18 komorkach.

TYLKO ODCZYT - skrypt niczego nie zapisuje ani nie modyfikuje.
Uruchamiac z katalogu glownego repo:
  .venv/Scripts/python.exe analysis/success_flag_gap.py
"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CELLS = [
    ("bielik-11b-v3", "Q2_K", "results/v3_11b_2026-06-18/q2_no_repair"),
    ("bielik-11b-v3", "Q3_K_M", "results/v3_11b_2026-06-18/q3_no_repair"),
    ("bielik-11b-v3", "Q4_K_M", "results/v3_11b_2026-06-18/q4_no_repair"),
    ("bielik-11b-v3", "Q5_K_M", "results/v3_11b_2026-06-18/q5_no_repair"),
    ("bielik-11b-v3", "Q6_K", "results/v3_11b_2026-06-18/q6_no_repair"),
    ("bielik-11b-v3", "Q8_0", "results/v3_11b_2026-06-18/q8_no_repair"),
    ("bielik-minitron-7b-v3", "Q2_K", "results/v3_arith_clean_2026-06-18/q2_no_repair"),
    ("bielik-minitron-7b-v3", "Q3_K_M", "results/v3_arith_clean_2026-06-18/q3_no_repair"),
    ("bielik-minitron-7b-v3", "Q4_K_M", "results/v3_arith_clean_2026-06-18/q4_no_repair"),
    ("bielik-minitron-7b-v3", "Q5_K_M", "results/v3_7b_grid_2026-07-29/q5_no_repair"),
    ("bielik-minitron-7b-v3", "Q6_K", "results/v3_7b_grid_2026-07-29/q6_no_repair"),
    ("bielik-minitron-7b-v3", "Q8_0", "results/v3_arith_clean_2026-06-18/q8_no_repair"),
    ("llama-pllum-8b", "Q2_K", "results/v3_pllum_2026-07-29/q2_main_no_repair"),
    ("llama-pllum-8b", "Q3_K_M", "results/v3_pllum_2026-07-29/q3_main_no_repair"),
    ("llama-pllum-8b", "Q4_K_M", "results/v3_pllum_2026-07-29/q4_main_no_repair"),
    ("llama-pllum-8b", "Q5_K_M", "results/v3_pllum_2026-07-29/q5_main_no_repair"),
    ("llama-pllum-8b", "Q6_K", "results/v3_pllum_2026-07-29/q6_main_no_repair"),
    ("llama-pllum-8b", "Q8_0", "results/v3_pllum_2026-07-29/q8_main_no_repair"),
]

print("=== FLAGA trajectory.success WOBEC ORACLE - main67, repair=off ===")
print(f"{'model':<24}{'kwant':<8}{'oracle':>10}{'flaga':>10}{'roznica':>10}   katalog")
print("-" * 108)
zawyza = niezgodne = 0
for model, quant, run in CELLS:
    sm = json.load(open(os.path.join(run, "summary.json"), encoding="utf-8"))
    flag = sum(1 for l in open(os.path.join(run, "trajectories.jsonl"), encoding="utf-8")
               if json.loads(l)["success"])
    orc, n = sm["num_passed"], sm["num_total"]
    niezgodne += (sm.get("model_id") != model or sm.get("quant") != quant or n != 67)
    zawyza += (flag > orc)
    print(f"{model:<24}{quant:<8}{str(orc) + '/' + str(n):>10}{str(flag) + '/' + str(n):>10}"
          f"{flag - orc:>+10}   {os.path.normpath(run)}")
print("-" * 108)
print(f"komorek, w ktorych flaga ZAWYZA wynik: {zawyza} z {len(CELLS)}")
print(f"komorek o niezgodnym opisie (model_id / kwant / n != 67): {niezgodne}")
