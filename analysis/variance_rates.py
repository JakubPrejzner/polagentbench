# -*- coding: utf-8 -*-
"""
Wariancja: pass rate szesciu runow seedowych z czterema miejscami po przecinku.

CO LICZY:
Dla szesciu runow z results/v3_11b_variance_2026-07-29 (Q8_0 i Q3_K_M, po trzy seedy)
wypisuje num_passed/num_total oraz success_rate z summary.json z czterema miejscami po
przecinku - to jest kolumna "Rate" w tabeli wariancji, ktorej zaden inny skrypt nie drukuje
(variance_seed_config.py drukuje tylko passed). Kazdy wiersz jest walidowany: success_rate
z pliku musi zgadzac sie z ilorazem num_passed/num_total do czwartego miejsca, inaczej
wiersz dostaje ROZJAZD. Na koncu wypisany jest rozstep (max minus min) w obrebie kwantyzacji,
czyli wiersz "Spread" tabeli.

CZYTA Z:
  results/v3_11b_variance_2026-07-29/{q8,q3}_seed{1,2,3}/summary.json

PRODUKUJE:
  paper/tables/variance.tex (tab:variance): kolumny Pass/n i Rate oraz ich rozstepy.

TYLKO ODCZYT - skrypt niczego nie zapisuje ani nie modyfikuje.
Uruchamiac z katalogu glownego repo:
  .venv/Scripts/python.exe analysis/variance_rates.py
"""
import json, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "results/v3_11b_variance_2026-07-29"
GROUPS = [("Q8_0", ["q8_seed1", "q8_seed2", "q8_seed3"]),
          ("Q3_K_M", ["q3_seed1", "q3_seed2", "q3_seed3"])]

print("=== PASS RATE SEEDOW (success_rate z summary.json, 4 miejsca po przecinku) ===")
print(f"{'kwant':<8}{'katalog':<12}{'pass/n':>10}{'Rate':>10}{'iloraz':>10}  walidacja")
print("-" * 62)
rozjazdy = 0
spread = {}
for quant, runs in GROUPS:
    rates, passed = [], []
    for r in runs:
        sm = json.load(open(f"{BASE}/{r}/summary.json", encoding="utf-8"))
        npass, ntot = sm["num_passed"], sm["num_total"]
        rate = sm["success_rate"]
        quot = npass / ntot
        ok = round(rate, 4) == round(quot, 4)
        rozjazdy += (not ok)
        rates.append(round(rate, 4)); passed.append(npass)
        print(f"{quant:<8}{r:<12}{str(npass) + '/' + str(ntot):>10}{rate:>10.4f}{quot:>10.4f}  "
              f"{'OK' if ok else 'ROZJAZD'}")
    spread[quant] = (max(passed) - min(passed), max(rates) - min(rates))
print()
print("=== ROZSTEP (max minus min) W OBREBIE KWANTYZACJI ===")
print(f"{'kwant':<10}{'pass [zadan]':>14}{'Rate':>10}")
print("-" * 34)
for quant, _ in GROUPS:
    dp, dr = spread[quant]
    print(f"{quant:<10}{dp:>14}{dr:>10.4f}")
print()
print(f"ROZJAZDOW: {rozjazdy}  (0 = success_rate zgodny z num_passed/num_total w kazdym runie)")
