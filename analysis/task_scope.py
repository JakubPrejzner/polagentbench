# -*- coding: utf-8 -*-
"""
Zakres zadan: ile zadan w ogole podlega kontroli goldenow.

CO LICZY:
Liczy pliki tasks/**/*.yaml majace klucz expected_final_state - czyli dokladnie ten zbior,
po ktorym chodzi kontrola negatywna w attractor59_negative_controls.py - i rozbija go na
katalogi: tasks/adversarial (suite main67), tasks/ladder_ext (suite ladder46), tasks/smoke,
tasks/_examples. Wynik: 119 zadan = 67 + 46 + 5 + 1. Ta liczba jest MIANOWNIKIEM zdania
"golden 59 w 0 ze 119 sprawdzonych zadan" - sam licznik (0) tez jest tu wypisany, zeby cala
komorka tabeli pochodzila z jednego wydruku. Kontrola jest wiec szersza niz sama suite main67.

CZYTA Z:
  tasks/**/*.yaml

PRODUKUJE:
  paper/tables/attractor.tex (tab:attractor_scope): wiersz "Tasks whose golden answer is
  59 / 59.0 / 59,0 -> 0 of 119 tasks checked" oraz rozbicie 67 / 46 / 5 / 1 w przypisie.

TYLKO ODCZYT - skrypt niczego nie zapisuje ani nie modyfikuje.
Uruchamiac z katalogu glownego repo:
  .venv/Scripts/python.exe analysis/task_scope.py
"""
import glob, os, sys, collections, yaml
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SUITE = {"adversarial": "main67", "ladder_ext": "ladder46", "smoke": "smoke5", "_examples": "-"}
GOLD59 = ("59", "59.0", "59,0")

per_dir = collections.Counter()
gold59 = []
total = 0
for f in sorted(glob.glob("tasks/**/*.yaml", recursive=True)):
    try:
        d = yaml.safe_load(open(f, encoding="utf-8"))
    except Exception:
        continue
    if not isinstance(d, dict) or "expected_final_state" not in d:
        continue
    total += 1
    parts = os.path.normpath(f).split(os.sep)
    per_dir[parts[1] if len(parts) > 2 else "(tasks/)"] += 1
    g = (d["expected_final_state"] or {}).get("final_answer_contains_any") or []
    if any(str(x).strip() in GOLD59 for x in g):
        gold59.append(d.get("id", f))

print("=== ZADANIA Z KLUCZEM expected_final_state (zbior kontrolowany) ===")
print(f"{'katalog':<22}{'suite':>10}{'zadan':>8}")
print("-" * 40)
for k in sorted(per_dir):
    print(f"tasks/{k:<16}{SUITE.get(k, '?'):>10}{per_dir[k]:>8}")
print("-" * 40)
print(f"{'RAZEM':<22}{'':>10}{total:>8}")
print()
print("=== KONTROLA NEGATYWNA: czy 59 jest goldenem ktoregokolwiek z tych zadan ===")
print(f"  zadan z goldenem 59 / 59.0 / 59,0: {len(gold59)} z {total} sprawdzonych   {gold59}")
