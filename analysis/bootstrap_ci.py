# -*- coding: utf-8 -*-
"""
Podloga szumu: bootstrap CI 95% dla 18 komorek krzywej glownej (suite main67).

CO LICZY:
Dla kazdej komorki model x kwant na suicie main67 buduje wektor 0/1 dlugosci 67 (jedno
zadanie = jedna obserwacja) i liczy percentylowy przedzial ufnosci 95% dla pass rate,
losujac ze zwracaniem PO ZADANIACH (nie po krokach, nie po trajektoriach), 10 000 prob.
Ziarno jest ustalone na sztywno: SEED = 42, przekazywane jako rng_seed do
polagentbench.eval.stats.bootstrap_ci, ktory tworzy random.Random(SEED) osobno dla kazdej
komorki - wynik jest odtwarzalny co do cyfry i nie zalezy od kolejnosci komorek. Wektor
jest zawsze uporzadkowany rosnaco po task_id (kolejnosc wplywa na konkretne losowania).
Werdykty pochodza WYLACZNIE z oracle: z run.log tam gdzie run.log istnieje, a tam gdzie
go nie ma - z odtworzenia kodem repo przez eval.smoke.evaluate. Pole trajectory.success
NIE jest uzywane nigdzie. Kazda komorka przechodzi walidacje: dlugosc wektora == 67 oraz
suma jedynek == summary.json:num_passed; rozjazd jest wypisywany jako ROZJAZD i liczony.
Wydruk konczy sie dwoma porownaniami: (a) czy przedzialy Q8/Q6/Q5 nachodza na siebie
w obrebie modelu, (b) o ile punktow procentowych spadek Q3->Q2 przekracza szerokosc
szerszego z dwoch przedzialow.

Odtwarzanie kodem HEAD jest legalne dla wszystkich komorek krzywej main67, bo
'git diff --stat <commit> HEAD -- tasks/adversarial src/polagentbench/eval' jest pusty
dla a023c3b, 83db813 i e584b38.

CZYTA Z:
  results/v3_11b_2026-06-18/q{2,3,4,5,6,8}_{no_repair,repair}/{trajectories.jsonl,summary.json}
  results/v3_arith_clean_2026-06-18/q{2,3,4,8}_{no_repair,repair}/{trajectories.jsonl,summary.json}
  results/v3_7b_grid_2026-07-29/q{5,6}_{no_repair,repair}/{run.log,summary.json}
  results/v3_pllum_2026-07-29/q{2,3,4,5,6,8}_main_{no_repair,repair}/{run.log,summary.json}
  tasks/adversarial/*.yaml, src/polagentbench/ (eval.smoke.evaluate, eval.stats.bootstrap_ci)

PRODUKUJE:
  Sekcja "Podloga szumu: bootstrap CI 95%": TABELA CI repair=off (obowiazkowa),
  TABELA CI repair=ON, blok porownan (a) Q8/Q6/Q5 i (b) Q3->Q2.

TYLKO ODCZYT - skrypt niczego nie zapisuje ani nie modyfikuje.
Uruchamiac z katalogu glownego repo:
  .venv/Scripts/python.exe analysis/bootstrap_ci.py
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, "src")
from polagentbench.eval.smoke import SmokeStatus, evaluate  # noqa: E402
from polagentbench.eval.stats import bootstrap_ci  # noqa: E402
from polagentbench.io import load_all_tasks  # noqa: E402
from polagentbench.types import Trajectory  # noqa: E402

SEED = 42                # ziarno na sztywno - patrz docstring.
                         # 42 jest ziarnem, przy ktorym policzono WSZYSTKIE przedzialy
                         # raportowane w paperze (tab:boot-point i tab:boot-diff);
                         # zmiana tej wartosci rozjedzie skrypt z papierem.
N_RESAMPLES = 10000      # liczba prob bootstrapu
ALPHA = 0.05             # przedzial 95%
N_TASKS = 67             # suite main67 = tasks/adversarial/*.yaml

# (model, kwant, katalog repair=off, katalog repair=ON)
KOMORKI = [
    ("bielik-11b-v3", "Q2_K",
     "results/v3_11b_2026-06-18/q2_no_repair", "results/v3_11b_2026-06-18/q2_repair"),
    ("bielik-11b-v3", "Q3_K_M",
     "results/v3_11b_2026-06-18/q3_no_repair", "results/v3_11b_2026-06-18/q3_repair"),
    ("bielik-11b-v3", "Q4_K_M",
     "results/v3_11b_2026-06-18/q4_no_repair", "results/v3_11b_2026-06-18/q4_repair"),
    ("bielik-11b-v3", "Q5_K_M",
     "results/v3_11b_2026-06-18/q5_no_repair", "results/v3_11b_2026-06-18/q5_repair"),
    ("bielik-11b-v3", "Q6_K",
     "results/v3_11b_2026-06-18/q6_no_repair", "results/v3_11b_2026-06-18/q6_repair"),
    ("bielik-11b-v3", "Q8_0",
     "results/v3_11b_2026-06-18/q8_no_repair", "results/v3_11b_2026-06-18/q8_repair"),
    ("bielik-minitron-7b-v3", "Q2_K",
     "results/v3_arith_clean_2026-06-18/q2_no_repair",
     "results/v3_arith_clean_2026-06-18/q2_repair"),
    ("bielik-minitron-7b-v3", "Q3_K_M",
     "results/v3_arith_clean_2026-06-18/q3_no_repair",
     "results/v3_arith_clean_2026-06-18/q3_repair"),
    ("bielik-minitron-7b-v3", "Q4_K_M",
     "results/v3_arith_clean_2026-06-18/q4_no_repair",
     "results/v3_arith_clean_2026-06-18/q4_repair"),
    ("bielik-minitron-7b-v3", "Q5_K_M",
     "results/v3_7b_grid_2026-07-29/q5_no_repair", "results/v3_7b_grid_2026-07-29/q5_repair"),
    ("bielik-minitron-7b-v3", "Q6_K",
     "results/v3_7b_grid_2026-07-29/q6_no_repair", "results/v3_7b_grid_2026-07-29/q6_repair"),
    ("bielik-minitron-7b-v3", "Q8_0",
     "results/v3_arith_clean_2026-06-18/q8_no_repair",
     "results/v3_arith_clean_2026-06-18/q8_repair"),
    ("llama-pllum-8b", "Q2_K",
     "results/v3_pllum_2026-07-29/q2_main_no_repair",
     "results/v3_pllum_2026-07-29/q2_main_repair"),
    ("llama-pllum-8b", "Q3_K_M",
     "results/v3_pllum_2026-07-29/q3_main_no_repair",
     "results/v3_pllum_2026-07-29/q3_main_repair"),
    ("llama-pllum-8b", "Q4_K_M",
     "results/v3_pllum_2026-07-29/q4_main_no_repair",
     "results/v3_pllum_2026-07-29/q4_main_repair"),
    ("llama-pllum-8b", "Q5_K_M",
     "results/v3_pllum_2026-07-29/q5_main_no_repair",
     "results/v3_pllum_2026-07-29/q5_main_repair"),
    ("llama-pllum-8b", "Q6_K",
     "results/v3_pllum_2026-07-29/q6_main_no_repair",
     "results/v3_pllum_2026-07-29/q6_main_repair"),
    ("llama-pllum-8b", "Q8_0",
     "results/v3_pllum_2026-07-29/q8_main_no_repair",
     "results/v3_pllum_2026-07-29/q8_main_repair"),
]

MODELE = ["bielik-11b-v3", "bielik-minitron-7b-v3", "llama-pllum-8b"]

TASKS = {t.id: t for t in load_all_tasks(Path("tasks/adversarial"))}


def werdykty_z_run_log(katalog):
    """Oracle z run.log. Format wiersza: '<task_id> <znak> <slad> [- tagi]'."""
    verd = {}
    with open(f"{katalog}/run.log", encoding="utf-8") as fh:
        for ln in fh:
            m = re.match(r"^(\S+)\s+([✓✗?])\s+(.*)$", ln.rstrip("\n"))
            if m:
                verd[m.group(1)] = 1 if m.group(2) == "✓" else 0
    return verd


def werdykty_odtworzone(katalog):
    """Oracle odtworzony kodem repo: eval.smoke.evaluate na kazdej trajektorii."""
    verd = {}
    with open(f"{katalog}/trajectories.jsonl", encoding="utf-8") as fh:
        for ln in fh:
            tr = Trajectory.model_validate(json.loads(ln))
            sr = evaluate(TASKS[tr.task_id], tr)
            verd[tr.task_id] = 1 if sr.status is SmokeStatus.PASS else 0
    return verd


def wektor_komorki(katalog):
    """Zwraca (wektor 0/1 posortowany po task_id, zrodlo werdyktow, num_passed z summary)."""
    if Path(f"{katalog}/run.log").exists():
        verd = werdykty_z_run_log(katalog)
        zrodlo = "run.log"
    else:
        verd = werdykty_odtworzone(katalog)
        zrodlo = "odtworzone (eval.smoke)"
    with open(f"{katalog}/summary.json", encoding="utf-8") as fh:
        num_passed = json.load(fh)["num_passed"]
    wektor = [verd[tid] for tid in sorted(verd)]
    return wektor, zrodlo, num_passed


def policz(kolumna_katalogow):
    """Buduje wektory, waliduje je i liczy CI. Zwraca (wyniki, liczba rozjazdow)."""
    wyniki = {}
    rozjazdy = 0
    for model, kwant, kat_off, kat_on in KOMORKI:
        katalog = kat_off if kolumna_katalogow == "off" else kat_on
        wektor, zrodlo, num_passed = wektor_komorki(katalog)
        suma = sum(wektor)
        n = len(wektor)
        ok_dl = n == N_TASKS
        ok_sum = suma == num_passed
        if not (ok_dl and ok_sum):
            rozjazdy += 1
            print(f"  ROZJAZD  {model:<22}{kwant:<8} {katalog}")
            print(f"           dlugosc wektora={n} (oczekiwano {N_TASKS}), "
                  f"suma jedynek={suma}, summary.num_passed={num_passed}, zrodlo={zrodlo}")
        else:
            print(f"  OK       {model:<22}{kwant:<8} n={n}  suma={suma}  "
                  f"summary.num_passed={num_passed}  zrodlo={zrodlo}")
        lo, hi = bootstrap_ci(wektor, n_resamples=N_RESAMPLES, alpha=ALPHA, rng_seed=SEED)
        wyniki[(model, kwant)] = {
            "pass": suma, "n": n, "rate": suma / n,
            "lo": lo, "hi": hi, "szer": hi - lo,
            "zrodlo": zrodlo, "katalog": katalog,
        }
    return wyniki, rozjazdy


def drukuj_tabele(naglowek, wyniki):
    print()
    print(naglowek)
    print(f"{'model':<24}{'kwant':<8}{'pass':>6}{'n':>5}{'rate':>9}"
          f"{'CI_low':>9}{'CI_high':>9}{'szer.CI':>9}   zrodlo werdyktow")
    print("-" * 108)
    for model in MODELE:
        for _mod, kwant, _a, _b in [k for k in KOMORKI if k[0] == model]:
            w = wyniki[(model, kwant)]
            print(f"{model:<24}{kwant:<8}{w['pass']:>6}{w['n']:>5}{w['rate']:>9.3f}"
                  f"{w['lo']:>9.3f}{w['hi']:>9.3f}{w['szer']:>9.3f}   {w['zrodlo']}")


def drukuj_porownania(wyniki):
    print()
    print("=== (a) czy przedzialy Q8, Q6, Q5 nachodza na siebie w obrebie modelu ===")
    for model in MODELE:
        print(f"  {model}")
        trojka = ["Q8_0", "Q6_K", "Q5_K_M"]
        for i in range(len(trojka)):
            for j in range(i + 1, len(trojka)):
                a, b = wyniki[(model, trojka[i])], wyniki[(model, trojka[j])]
                lo = max(a["lo"], b["lo"])
                hi = min(a["hi"], b["hi"])
                if hi >= lo:
                    czesc = f"NACHODZA, czesc wspolna [{lo:.3f}, {hi:.3f}] szer. {hi - lo:.3f}"
                else:
                    czesc = f"ROZLACZNE, przerwa {lo - hi:.3f}"
                print(f"    {trojka[i]:<7}[{a['lo']:.3f}, {a['hi']:.3f}]  vs  "
                      f"{trojka[j]:<7}[{b['lo']:.3f}, {b['hi']:.3f}]   "
                      f"roznica rate {a['rate'] - b['rate']:+.3f}   {czesc}")
        lo3 = max(wyniki[(model, q)]["lo"] for q in trojka)
        hi3 = min(wyniki[(model, q)]["hi"] for q in trojka)
        if hi3 >= lo3:
            print(f"    -> cala trojka ma czesc wspolna [{lo3:.3f}, {hi3:.3f}] "
                  f"szer. {hi3 - lo3:.3f}")
        else:
            print(f"    -> cala trojka NIE ma czesci wspolnej (przerwa {lo3 - hi3:.3f})")

    print()
    print("=== (b) o ile pp spadek Q3->Q2 przekracza szerokosc szerszego z dwoch CI ===")
    print(f"{'model':<24}{'rate Q3':>9}{'rate Q2':>9}{'spadek pp':>11}"
          f"{'szer.CI Q3 pp':>15}{'szer.CI Q2 pp':>15}{'szerszy pp':>12}{'nadwyzka pp':>13}{'krotnosc':>10}")
    print("-" * 118)
    for model in MODELE:
        q3, q2 = wyniki[(model, "Q3_K_M")], wyniki[(model, "Q2_K")]
        spadek = (q3["rate"] - q2["rate"]) * 100
        w3, w2 = q3["szer"] * 100, q2["szer"] * 100
        szerszy = max(w3, w2)
        print(f"{model:<24}{q3['rate']:>9.3f}{q2['rate']:>9.3f}{spadek:>11.1f}"
              f"{w3:>15.1f}{w2:>15.1f}{szerszy:>12.1f}{spadek - szerszy:>13.1f}"
              f"{spadek / szerszy:>10.2f}x")


print("=== PODLOGA SZUMU: bootstrap percentylowy CI 95%, resampling PO ZADANIACH ===")
print(f"ziarno (SEED) = {SEED}   prob bootstrapu = {N_RESAMPLES}   alpha = {ALPHA}   "
      f"suite = main67 (n = {N_TASKS} zadan)")
print(f"zadan zaladowanych z tasks/adversarial: {len(TASKS)}")
print("werdykty: oracle (run.log albo eval.smoke.evaluate); trajectory.success NIE uzywane")
print("wektor uporzadkowany rosnaco po task_id; random.Random(SEED) tworzony osobno dla komorki")

print()
print("=== WALIDACJA wektorow 0/1 wobec summary.json (repair=off) ===")
wyn_off, rozj_off = policz("off")
print(f"  rozjazdow repair=off: {rozj_off}")

print()
print("=== WALIDACJA wektorow 0/1 wobec summary.json (repair=ON) ===")
wyn_on, rozj_on = policz("on")
print(f"  rozjazdow repair=ON: {rozj_on}")

drukuj_tabele("=== TABELA CI — repair=off (krzywa glowna, obowiazkowa) ===", wyn_off)
drukuj_tabele("=== TABELA CI — repair=ON (tabela dodatkowa) ===", wyn_on)

print()
print("### POROWNANIA LICZONE NA repair=off ###")
drukuj_porownania(wyn_off)

print()
print(f"ROZJAZDOW LACZNIE: {rozj_off + rozj_on}  "
      f"(0 = kazdy wektor zgodny z summary.json i dlugosci {N_TASKS})")
