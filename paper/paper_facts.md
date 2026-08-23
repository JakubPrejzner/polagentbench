# paper_facts.md — liczby do papera, odtworzone z danych

**Data wygenerowania:** 2026-08-23
**Repo:** `polagentbench`, branch `main`, HEAD `6c4f241`
**GPU:** nieużywane. Każda liczba poniżej powstała z danych, które już leżały na dysku.

Każda tabela w tym pliku jest **odtworzona skryptami z `analysis/`**, nie przepisana z
żadnego `.tex`. Przy każdej tabeli podany jest skrypt źródłowy i plik wejściowy.

## Jak to zostało policzone

Wszystkie 24 skrypty z `analysis/` zostały uruchomione z katalogu głównego repo
interpreterem `.venv/Scripts/python.exe`; wszystkie zakończyły się kodem 0 z pustym
stderr. Sekcje poniżej cytują ich wydruki.

**Legalność odtwarzania werdyktów.** Część katalogów wynikowych nie ma `run.log`, więc
werdykty oracle odtwarzane są kodem HEAD (`polagentbench.eval.smoke.evaluate`). Warunek,
który to legalizuje, został sprawdzony: `git diff --stat <commit> HEAD -- tasks/adversarial
src/polagentbench/eval` jest **pusty** dla `a023c3b`, `83db813` i `e584b38` — czyli dla
wszystkich 18 komórek krzywej `main67`. Dla `ef122d4`, `d6088b3` i `1b1af70` ten diff
**nie** jest pusty; na tych przebiegach wolno wyłącznie czytać zapisane `summary.json` /
`run.log`, i tak też zrobiono (sekcja o rozjazdach).

**Oracle, nie flaga.** Żadna liczba nie pochodzi z `trajectory.success` — ta flaga zawyża
w każdej z 36 komórek, skrajnie u PLLuM Q8 (flaga 66/67 wobec oracle 13/67).

**Weryfikacja.** Liczby w wygenerowanych tabelach `paper/tables/*.tex` zostały niezależnie
sprawdzone wobec tych sekcji: 1048 sprawdzonych pozycji, 0 błędów liczbowych.

---



<!-- source section: 01_krzywa.md -->

## Krzywa kwantyzacji (main67, 6 kwantow x 3 modele)

### 0. Zakres i definicje

- Suite: `main67` = `tasks/adversarial/*.yaml`. Zweryfikowane: `ls tasks/adversarial/*.yaml | wc -l` = **67**.
- 18 komorek = 3 modele x 6 kwantow (Q2_K, Q3_K_M, Q4_K_M, Q5_K_M, Q6_K, Q8_0), kazda w dwoch wariantach
  `repair=off` i `repair=ON` -> **36 katalogow runow**.
- Mianownik n = `num_tasks` z `summary.json`. We wszystkich 36 katalogach:
  `num_tasks = num_total = num_trajectories = 67`, `num_inconclusive = 0`.
  (zrodlo: `summary.json` kazdego z 36 katalogow, odczyt bezposredni)
- Pass rate = `num_passed / num_tasks`, zaokraglone do 3 miejsc.
- Werdykt = oracle (`num_passed` z `summary.json`), **nie** `trajectory.success`. Roznica jest duza,
  patrz sekcja 2a.

---

### 1. TABELA 1 -- 18 komorek, repair=off i repair=ON

Zrodlo liczb: pole `num_passed` / `num_tasks` z `summary.json` w kazdym z 36 katalogow
(pelna lista katalogow w TABELI 6 -- prowenancja).
Konfrontacja: `analysis/inventory.py`, wyjscie w
`scratchpad/analysis_out/inventory.txt`, wiersze z kolumna `suite = main67`.

| Model | Kwant | repair=off zdane | n | pass rate off | repair=ON zdane | n | pass rate ON |
|---|---|---|---|---|---|---|---|
| bielik-11b-v3 | Q2_K   | 3  | 67 | 0.045 | 5  | 67 | 0.075 |
| bielik-11b-v3 | Q3_K_M | 48 | 67 | 0.716 | 48 | 67 | 0.716 |
| bielik-11b-v3 | Q4_K_M | 36 | 67 | 0.537 | 40 | 67 | 0.597 |
| bielik-11b-v3 | Q5_K_M | 50 | 67 | 0.746 | 51 | 67 | 0.761 |
| bielik-11b-v3 | Q6_K   | 56 | 67 | 0.836 | 57 | 67 | 0.851 |
| bielik-11b-v3 | Q8_0   | 54 | 67 | 0.806 | 54 | 67 | 0.806 |
| bielik-minitron-7b-v3 | Q2_K   | 10 | 67 | 0.149 | 12 | 67 | 0.179 |
| bielik-minitron-7b-v3 | Q3_K_M | 31 | 67 | 0.463 | 31 | 67 | 0.463 |
| bielik-minitron-7b-v3 | Q4_K_M | 34 | 67 | 0.507 | 40 | 67 | 0.597 |
| bielik-minitron-7b-v3 | Q5_K_M | 35 | 67 | 0.522 | 40 | 67 | 0.597 |
| bielik-minitron-7b-v3 | Q6_K   | 31 | 67 | 0.463 | 38 | 67 | 0.567 |
| bielik-minitron-7b-v3 | Q8_0   | 30 | 67 | 0.448 | 38 | 67 | 0.567 |
| llama-pllum-8b | Q2_K   | 1  | 67 | 0.015 | 1  | 67 | 0.015 |
| llama-pllum-8b | Q3_K_M | 15 | 67 | 0.224 | 18 | 67 | 0.269 |
| llama-pllum-8b | Q4_K_M | 15 | 67 | 0.224 | 17 | 67 | 0.254 |
| llama-pllum-8b | Q5_K_M | 7  | 67 | 0.104 | 9  | 67 | 0.134 |
| llama-pllum-8b | Q6_K   | 12 | 67 | 0.179 | 14 | 67 | 0.209 |
| llama-pllum-8b | Q8_0   | 13 | 67 | 0.194 | 15 | 67 | 0.224 |

Pole `success_rate` zapisane w `summary.json` (4 miejsca) zgadza sie z `num_passed/num_tasks`
we wszystkich 36 przypadkach, np. 0.0448 / 0.7164 / 0.8358 / 0.0149.

---

### 2. Kontrola zgodnosci zrodel -- ROZJAZDY

Sprawdzone cztery zrodla werdyktu na tych samych 36 katalogach.

| Zrodlo | Co to jest | Pokrycie | Wynik konfrontacji z `summary.json` |
|---|---|---|---|
| `summary.json` -> `num_passed` | zapis z chwili runu | 36/36 | (referencja) |
| `analysis/inventory.py` -> kolumna `wynik` | odczyt `summary.json` | 36/36 | **zgodne 36/36** |
| `eval.smoke.evaluate()` na `trajectories.jsonl` kodem HEAD (6c4f241) | odtworzenie oracle | 36/36 | **zgodne 36/36, ROZJAZDOW BRAK** |
| `run.log` -> linia `Success: X/67` | oracle zapisany podczas runu | 16/36 | **zgodne 16/16** |

Uwaga metodologiczna (zeby nie przecenic zgodnosci nr 2): `analysis/inventory.py` czyta
`d.get("num_passed")` i `d.get("num_total")` prosto z `summary.json` -- jego zgodnosc z
`summary.json` jest **z konstrukcji**, nie jest niezaleznym potwierdzeniem. Niezalezne sa dopiero
wiersze 3 i 4 tabeli.

Odtworzenie oracle kodem HEAD jest legalne dla wszystkich 18 komorek krzywej, bo
`git diff --stat <commit> HEAD -- tasks/adversarial src/polagentbench/eval` jest **pusty** dla
a023c3b, 83db813 i e584b38 (sprawdzone ponownie w tej sesji, wszystkie trzy diffy puste).

**ROZJAZDY: BRAK.** Zaden z 36 katalogow nie wykazal roznicy miedzy `summary.json`,
`inventory.py`, odtworzonym oracle i `run.log`.

Wartosci `Success:` odczytane z 16 `run.log` (pelna lista, zgodne co do jednego z TABELA 1):
7B Q5 off 35/67, 7B Q5 ON 40/67, 7B Q6 off 31/67, 7B Q6 ON 38/67;
PLLuM Q2 off 1/67, Q2 ON 1/67, Q3 off 15/67, Q3 ON 18/67, Q4 off 15/67, Q4 ON 17/67,
Q5 off 7/67, Q5 ON 9/67, Q6 off 12/67, Q6 ON 14/67, Q8 off 13/67, Q8 ON 15/67.
Dodatkowa kontrola: liczba znakow `✓` w kazdym `run.log` rowna sie liczbie z linii `Success:`
we wszystkich 16 plikach.

Skrypt kontrolny (napisany na potrzeby tej sekcji, poza repo, tylko odczyt):
`C:\Users\japre\AppData\Local\Temp\claude\C--Users-japre\0d10ab87-df8a-4796-ae51-3a459845031f\scratchpad\verify_curve.py`
-- wypisuje kolumny `sum` / `reeval` / `flaga` / `runlog` / `n` i konczy linia
`ROZJAZDY summary vs re-eval: BRAK`.

#### 2a. Dlaczego nie `trajectory.success` (kolumna "flaga")

Ta sama kontrola policzyla `sum(tr.success)` z `trajectories.jsonl`. Flaga zawyza w **kazdej**
z 36 komorek. Rozstep skrajny -- llama-pllum-8b Q8_0 repair=off: flaga **66/67**, oracle **13/67**
(zrodlo: `results/v3_pllum_2026-07-29/q8_main_no_repair/trajectories.jsonl` +
`run.log`, linia `Success: 13/67 (19%)`). Drugi skrajny: llama-pllum-8b Q2_K repair=off,
flaga **65/67**, oracle **1/67**. Pelna kolumna "flaga" dla 36 katalogow jest w wyjsciu
`verify_curve.py`.

---

### 3. TABELA 2 -- delty miedzy sasiednimi kwantami (Q8 -> Q6 -> Q5 -> Q4 -> Q3 -> Q2)

Zrodlo: `num_passed` z `summary.json` 36 katalogow; przeliczenie skryptem
`C:\Users\japre\AppData\Local\Temp\claude\C--Users-japre\0d10ab87-df8a-4796-ae51-3a459845031f\scratchpad\deltas.py`.
Delta podana w zadaniach i w punktach procentowych (pp), mianownik zawsze 67.

**bielik-11b-v3**

| Przejscie | off: zdane | off: delta | off: pp | ON: zdane | ON: delta | ON: pp |
|---|---|---|---|---|---|---|
| Q8 -> Q6 | 54 -> 56 | +2  | +3.0  | 54 -> 57 | +3  | +4.5  |
| Q6 -> Q5 | 56 -> 50 | -6  | -9.0  | 57 -> 51 | -6  | -9.0  |
| Q5 -> Q4 | 50 -> 36 | -14 | -20.9 | 51 -> 40 | -11 | -16.4 |
| Q4 -> Q3 | 36 -> 48 | +12 | +17.9 | 40 -> 48 | +8  | +11.9 |
| Q3 -> Q2 | 48 -> 3  | -45 | -67.2 | 48 -> 5  | -43 | -64.2 |

**bielik-minitron-7b-v3**

| Przejscie | off: zdane | off: delta | off: pp | ON: zdane | ON: delta | ON: pp |
|---|---|---|---|---|---|---|
| Q8 -> Q6 | 30 -> 31 | +1  | +1.5  | 38 -> 38 | 0   | 0.0   |
| Q6 -> Q5 | 31 -> 35 | +4  | +6.0  | 38 -> 40 | +2  | +3.0  |
| Q5 -> Q4 | 35 -> 34 | -1  | -1.5  | 40 -> 40 | 0   | 0.0   |
| Q4 -> Q3 | 34 -> 31 | -3  | -4.5  | 40 -> 31 | -9  | -13.4 |
| Q3 -> Q2 | 31 -> 10 | -21 | -31.3 | 31 -> 12 | -19 | -28.4 |

**llama-pllum-8b**

| Przejscie | off: zdane | off: delta | off: pp | ON: zdane | ON: delta | ON: pp |
|---|---|---|---|---|---|---|
| Q8 -> Q6 | 13 -> 12 | -1  | -1.5  | 15 -> 14 | -1  | -1.5  |
| Q6 -> Q5 | 12 -> 7  | -5  | -7.5  | 14 -> 9  | -5  | -7.5  |
| Q5 -> Q4 | 7 -> 15  | +8  | +11.9 | 9 -> 17  | +8  | +11.9 |
| Q4 -> Q3 | 15 -> 15 | 0   | 0.0   | 17 -> 18 | +1  | +1.5  |
| Q3 -> Q2 | 15 -> 1  | -14 | -20.9 | 18 -> 1  | -17 | -25.4 |

---

### 4. TABELA 3 -- spadek Q3 -> Q2

| Model | repair | Q3 pass rate | Q2 pass rate | Spadek [pp] | Q2/Q3 (krotnosc) | Zadania |
|---|---|---|---|---|---|---|
| bielik-11b-v3 | off | 0.716 | 0.045 | **-67.2** | 0.062x | 48 -> 3 |
| bielik-11b-v3 | ON  | 0.716 | 0.075 | **-64.2** | 0.104x | 48 -> 5 |
| bielik-minitron-7b-v3 | off | 0.463 | 0.149 | **-31.3** | 0.323x | 31 -> 10 |
| bielik-minitron-7b-v3 | ON  | 0.463 | 0.179 | **-28.4** | 0.387x | 31 -> 12 |
| llama-pllum-8b | off | 0.224 | 0.015 | **-20.9** | 0.067x | 15 -> 1 |
| llama-pllum-8b | ON  | 0.269 | 0.015 | **-25.4** | 0.056x | 18 -> 1 |

Q3 -> Q2 jest najwiekszym co do wartosci bezwzglednej pojedynczym spadkiem krzywej u wszystkich
trzech modeli, w obu trybach repair (porownanie z TABELA 2: kolejny co do wielkosci spadek to
-20.9 pp, bielik-11b-v3 off Q5 -> Q4 -- co jest rowne spadkowi Q3->Q2 u PLLuM off).

---

### 5. TABELA 4 -- monotonicznosc

Kryterium: czy pass rate jest niemalejacy wzdluz Q2 -> Q3 -> Q4 -> Q5 -> Q6 -> Q8
(rosnaca szerokosc kwantu). Zlamanie = para sasiednich kwantow, w ktorej wyzszy kwant ma
**nizszy** pass rate.

| Model | repair | Monotoniczna? | Miejsca zlamania (rozmiar) | Maksimum krzywej |
|---|---|---|---|---|
| bielik-11b-v3 | off | **NIE** | Q3->Q4 (-17.9 pp); Q6->Q8 (-3.0 pp) | Q6 = 0.836 |
| bielik-11b-v3 | ON  | **NIE** | Q3->Q4 (-11.9 pp); Q6->Q8 (-4.5 pp) | Q6 = 0.851 |
| bielik-minitron-7b-v3 | off | **NIE** | Q5->Q6 (-6.0 pp); Q6->Q8 (-1.5 pp) | Q5 = 0.522 |
| bielik-minitron-7b-v3 | ON  | **NIE** | Q5->Q6 (-3.0 pp); remisy Q4=Q5 (0.597), Q6=Q8 (0.567) | Q4 = Q5 = 0.597 |
| llama-pllum-8b | off | **NIE** | Q4->Q5 (-11.9 pp); remis Q3=Q4 (0.224) | Q3 = Q4 = 0.224 |
| llama-pllum-8b | ON  | **NIE** | Q3->Q4 (-1.5 pp); Q4->Q5 (-11.9 pp) | Q3 = 0.269 |

Zadna z 6 krzywych (3 modele x 2 tryby repair) nie jest monotoniczna. W zadnej z 6 maksimum
nie wypada na Q8_0. Miejsca zlamania roznia sie miedzy modelami: 11B lamie sie na Q3->Q4
i Q6->Q8, 7B na Q5->Q6 i Q6->Q8, PLLuM na Q4->Q5 (oraz Q3->Q4 w trybie ON).

---

### 6. TABELA 5 -- efekt repair (ON minus off), na komorke

Zrodlo: te same pola `num_passed` z 36 plikow `summary.json`.

| Model | Q8 | Q6 | Q5 | Q4 | Q3 | Q2 |
|---|---|---|---|---|---|---|
| bielik-11b-v3 | 54->54 (0; 0.0 pp) | 56->57 (+1; +1.5 pp) | 50->51 (+1; +1.5 pp) | 36->40 (+4; +6.0 pp) | 48->48 (0; 0.0 pp) | 3->5 (+2; +3.0 pp) |
| bielik-minitron-7b-v3 | 30->38 (+8; +11.9 pp) | 31->38 (+7; +10.4 pp) | 35->40 (+5; +7.5 pp) | 34->40 (+6; +9.0 pp) | 31->31 (0; 0.0 pp) | 10->12 (+2; +3.0 pp) |
| llama-pllum-8b | 13->15 (+2; +3.0 pp) | 12->14 (+2; +3.0 pp) | 7->9 (+2; +3.0 pp) | 15->17 (+2; +3.0 pp) | 15->18 (+3; +4.5 pp) | 1->1 (0; 0.0 pp) |

Repair nie obniza liczby zdanych w zadnej z 18 komorek. Efekt zerowy w 4 komorkach:
bielik-11b-v3 Q8_0, bielik-11b-v3 Q3_K_M, bielik-minitron-7b-v3 Q3_K_M, llama-pllum-8b Q2_K.
Najwiekszy pojedynczy efekt: bielik-minitron-7b-v3 Q8_0, +8 zadan (+11.9 pp).

---

### 7. TABELA 6 -- prowenancja: komorka -> katalog -> commit -> run.log

`git_ref` i `commit_hash` czytane z `summary.json` kazdego katalogu.
Kolumna run.log: obecnosc pliku `run.log` w katalogu runu.
Wszystkie sciezki wzgledem `C:\Users\japre\polagentbench`.

| Model | Kwant | repair | Katalog | git_ref | commit_hash (pelny) | run.log |
|---|---|---|---|---|---|---|
| bielik-11b-v3 | Q2_K | off | `results/v3_11b_2026-06-18/q2_no_repair` | a023c3b | a023c3b2c239b57d700b174ac92b5d166c7e6f6a | BRAK |
| bielik-11b-v3 | Q2_K | ON | `results/v3_11b_2026-06-18/q2_repair` | a023c3b | a023c3b2c239b57d700b174ac92b5d166c7e6f6a | BRAK |
| bielik-11b-v3 | Q3_K_M | off | `results/v3_11b_2026-06-18/q3_no_repair` | a023c3b | a023c3b2c239b57d700b174ac92b5d166c7e6f6a | BRAK |
| bielik-11b-v3 | Q3_K_M | ON | `results/v3_11b_2026-06-18/q3_repair` | a023c3b | a023c3b2c239b57d700b174ac92b5d166c7e6f6a | BRAK |
| bielik-11b-v3 | Q4_K_M | off | `results/v3_11b_2026-06-18/q4_no_repair` | a023c3b | a023c3b2c239b57d700b174ac92b5d166c7e6f6a | BRAK |
| bielik-11b-v3 | Q4_K_M | ON | `results/v3_11b_2026-06-18/q4_repair` | a023c3b | a023c3b2c239b57d700b174ac92b5d166c7e6f6a | BRAK |
| bielik-11b-v3 | Q5_K_M | off | `results/v3_11b_2026-06-18/q5_no_repair` | a023c3b | a023c3b2c239b57d700b174ac92b5d166c7e6f6a | BRAK |
| bielik-11b-v3 | Q5_K_M | ON | `results/v3_11b_2026-06-18/q5_repair` | a023c3b | a023c3b2c239b57d700b174ac92b5d166c7e6f6a | BRAK |
| bielik-11b-v3 | Q6_K | off | `results/v3_11b_2026-06-18/q6_no_repair` | a023c3b | a023c3b2c239b57d700b174ac92b5d166c7e6f6a | BRAK |
| bielik-11b-v3 | Q6_K | ON | `results/v3_11b_2026-06-18/q6_repair` | a023c3b | a023c3b2c239b57d700b174ac92b5d166c7e6f6a | BRAK |
| bielik-11b-v3 | Q8_0 | off | `results/v3_11b_2026-06-18/q8_no_repair` | a023c3b | a023c3b2c239b57d700b174ac92b5d166c7e6f6a | BRAK |
| bielik-11b-v3 | Q8_0 | ON | `results/v3_11b_2026-06-18/q8_repair` | a023c3b | a023c3b2c239b57d700b174ac92b5d166c7e6f6a | BRAK |
| bielik-minitron-7b-v3 | Q2_K | off | `results/v3_arith_clean_2026-06-18/q2_no_repair` | 83db813 | 83db8131bbef8516b7f6ad7fbf1e0fd89c588ef1 | BRAK |
| bielik-minitron-7b-v3 | Q2_K | ON | `results/v3_arith_clean_2026-06-18/q2_repair` | 83db813 | 83db8131bbef8516b7f6ad7fbf1e0fd89c588ef1 | BRAK |
| bielik-minitron-7b-v3 | Q3_K_M | off | `results/v3_arith_clean_2026-06-18/q3_no_repair` | 83db813 | 83db8131bbef8516b7f6ad7fbf1e0fd89c588ef1 | BRAK |
| bielik-minitron-7b-v3 | Q3_K_M | ON | `results/v3_arith_clean_2026-06-18/q3_repair` | 83db813 | 83db8131bbef8516b7f6ad7fbf1e0fd89c588ef1 | BRAK |
| bielik-minitron-7b-v3 | Q4_K_M | off | `results/v3_arith_clean_2026-06-18/q4_no_repair` | 83db813 | 83db8131bbef8516b7f6ad7fbf1e0fd89c588ef1 | BRAK |
| bielik-minitron-7b-v3 | Q4_K_M | ON | `results/v3_arith_clean_2026-06-18/q4_repair` | 83db813 | 83db8131bbef8516b7f6ad7fbf1e0fd89c588ef1 | BRAK |
| bielik-minitron-7b-v3 | Q5_K_M | off | `results/v3_7b_grid_2026-07-29/q5_no_repair` | e584b38 | e584b38ec7045f37bfe3c42c402ca25995c8b2e7 | **JEST** |
| bielik-minitron-7b-v3 | Q5_K_M | ON | `results/v3_7b_grid_2026-07-29/q5_repair` | e584b38 | e584b38ec7045f37bfe3c42c402ca25995c8b2e7 | **JEST** |
| bielik-minitron-7b-v3 | Q6_K | off | `results/v3_7b_grid_2026-07-29/q6_no_repair` | e584b38 | e584b38ec7045f37bfe3c42c402ca25995c8b2e7 | **JEST** |
| bielik-minitron-7b-v3 | Q6_K | ON | `results/v3_7b_grid_2026-07-29/q6_repair` | e584b38 | e584b38ec7045f37bfe3c42c402ca25995c8b2e7 | **JEST** |
| bielik-minitron-7b-v3 | Q8_0 | off | `results/v3_arith_clean_2026-06-18/q8_no_repair` | 83db813 | 83db8131bbef8516b7f6ad7fbf1e0fd89c588ef1 | BRAK |
| bielik-minitron-7b-v3 | Q8_0 | ON | `results/v3_arith_clean_2026-06-18/q8_repair` | 83db813 | 83db8131bbef8516b7f6ad7fbf1e0fd89c588ef1 | BRAK |
| llama-pllum-8b | Q2_K | off | `results/v3_pllum_2026-07-29/q2_main_no_repair` | e584b38 | e584b38ec7045f37bfe3c42c402ca25995c8b2e7 | **JEST** |
| llama-pllum-8b | Q2_K | ON | `results/v3_pllum_2026-07-29/q2_main_repair` | e584b38 | e584b38ec7045f37bfe3c42c402ca25995c8b2e7 | **JEST** |
| llama-pllum-8b | Q3_K_M | off | `results/v3_pllum_2026-07-29/q3_main_no_repair` | e584b38 | e584b38ec7045f37bfe3c42c402ca25995c8b2e7 | **JEST** |
| llama-pllum-8b | Q3_K_M | ON | `results/v3_pllum_2026-07-29/q3_main_repair` | e584b38 | e584b38ec7045f37bfe3c42c402ca25995c8b2e7 | **JEST** |
| llama-pllum-8b | Q4_K_M | off | `results/v3_pllum_2026-07-29/q4_main_no_repair` | e584b38 | e584b38ec7045f37bfe3c42c402ca25995c8b2e7 | **JEST** |
| llama-pllum-8b | Q4_K_M | ON | `results/v3_pllum_2026-07-29/q4_main_repair` | e584b38 | e584b38ec7045f37bfe3c42c402ca25995c8b2e7 | **JEST** |
| llama-pllum-8b | Q5_K_M | off | `results/v3_pllum_2026-07-29/q5_main_no_repair` | e584b38 | e584b38ec7045f37bfe3c42c402ca25995c8b2e7 | **JEST** |
| llama-pllum-8b | Q5_K_M | ON | `results/v3_pllum_2026-07-29/q5_main_repair` | e584b38 | e584b38ec7045f37bfe3c42c402ca25995c8b2e7 | **JEST** |
| llama-pllum-8b | Q6_K | off | `results/v3_pllum_2026-07-29/q6_main_no_repair` | e584b38 | e584b38ec7045f37bfe3c42c402ca25995c8b2e7 | **JEST** |
| llama-pllum-8b | Q6_K | ON | `results/v3_pllum_2026-07-29/q6_main_repair` | e584b38 | e584b38ec7045f37bfe3c42c402ca25995c8b2e7 | **JEST** |
| llama-pllum-8b | Q8_0 | off | `results/v3_pllum_2026-07-29/q8_main_no_repair` | e584b38 | e584b38ec7045f37bfe3c42c402ca25995c8b2e7 | **JEST** |
| llama-pllum-8b | Q8_0 | ON | `results/v3_pllum_2026-07-29/q8_main_repair` | e584b38 | e584b38ec7045f37bfe3c42c402ca25995c8b2e7 | **JEST** |

Podsumowanie prowenancji: **16 z 36** katalogow ma `run.log` (4 x bielik-minitron-7b-v3 Q5/Q6,
12 x llama-pllum-8b), **20 z 36** nie ma. Krzywa siedzi na **trzech** commitach: a023c3b (12 katalogow),
83db813 (8), e584b38 (16). Model bielik-minitron-7b-v3 jest **rozdarty miedzy dwa commity i dwie daty
runu**: Q2/Q3/Q4/Q8 z katalogu z 2026-06-18 (83db813), Q5/Q6 z katalogu z 2026-07-29 (e584b38).
Pozostale dwa modele maja komplet 6 kwantow z jednego katalogu i jednego commitu.

Daty commitow (`git log -1 --format='%h %cd %s'`):

| Commit | Data | Tytul |
|---|---|---|
| a023c3b | 2026-06-18 20:51:17 +0200 | `run: clean arith + 67-task gradient` |
| 83db813 | 2026-06-18 19:02:30 +0200 | `fix(suite): rounding-robust goldens for all arith chains` |
| e584b38 | 2026-07-25 01:50:38 +0200 | `feat(ladder): extended ladder, 10 instances, dual L3 arm (trap and graph-free)` |
| 6c4f241 (HEAD) | 2026-08-21 21:57:26 +0200 | `chore: track suite validators, QA tool and run provenance` |

Legalnosc odtwarzania werdyktow kodem HEAD dla wszystkich 18 komorek:
`git diff --stat <commit> HEAD -- tasks/adversarial src/polagentbench/eval` = pusty dla a023c3b,
83db813 i e584b38 (sprawdzone w tej sesji).

#### 7a. Parametry runu

`summary.json` **nie zawiera** pol `seed`, `temperature`, `suite` ani `tasks_dir`.
Pelny zestaw kluczy (identyczny we wszystkich 36 plikach):
`commit_hash, failure_tag_counts, git_ref, model_id, num_inconclusive, num_passed, num_tasks,
num_total, num_trajectories, quant, repair, repair_applied_steps, success_rate`.

Seed i temperatura sa w rekordach `trajectories.jsonl`. Sprawdzone we wszystkich 36 katalogach
(skrypt
`C:\Users\japre\AppData\Local\Temp\claude\C--Users-japre\0d10ab87-df8a-4796-ae51-3a459845031f\scratchpad\seed_check.py`):
**seed = 42 w 67/67 rekordach, temperature = 0.0 w 67/67 rekordach, w kazdym z 36 katalogow**.
Rozklad wariantu interfejsu tez identyczny w kazdym z 36: `PL_EN = 49`, `EN_EN = 18`.
Dla 16 katalogow z `run.log` naglowek loga potwierdza niezaleznie, np.
`Smoke test results - llama-pllum-8b / Q8_0 / seed=42`.

---

### 8. BRAK DANYCH / ograniczenia liczb w tej sekcji

1. **Brak powtorzen dla komorek krzywej.** Kazda z 18 komorek (36 katalogow) = jeden przebieg,
   seed 42, temperature 0.0. Z danych na dysku **nie da sie policzyc odchylenia ani przedzialu
   ufnosci dla zadnej komorki tej krzywej** -- nie ma drugiego ani trzeciego przebiegu tych
   konkretnych konfiguracji.
2. Wyjatek czesciowy, poza krzywa: powtorzenia istnieja tylko dla bielik-11b-v3, tylko `repair=off`,
   tylko Q3_K_M i Q8_0, i **w innym katalogu, na innym commicie** --
   `results/v3_11b_variance_2026-07-29/q{3,8}_seed{1,2,3}` (commit e584b38, run.log JEST).
   Wartosci wg `inventory.txt`: Q3 seed1 13/67, seed2 43/67, seed3 51/67;
   Q8 seed1 8/67, seed2 49/67, seed3 48/67. To **inne przebiegi niz komorki krzywej**
   (krzywa: Q3 off = 48/67 z a023c3b, Q8 off = 54/67 z a023c3b) i nie zostaly do krzywej wliczone.
   Ich analiza nalezy do sekcji o wariancji, nie do tej.
3. **Brak `run.log` dla 20 z 36 katalogow** (wszystkie z a023c3b i 83db813). Dla nich oracle jest
   odtwarzany kodem HEAD; jest to legalne (puste diffy), ale nie jest to zapis z chwili runu.
4. Nie da sie z `summary.json` odczytac, ktory dokladnie plik GGUF ani jakie parametry llama.cpp
   byly uzyte -- pola tego nie ma. Dla 16 katalogow z `run.log` jest tylko linia
   `llama_context: n_ctx_seq (8192) < n_ctx_train (131072)`; dla pozostalych 20 **BRAK DANYCH**.
5. Roznica commitow miedzy Q2/Q3/Q4/Q8 (83db813) a Q5/Q6 (e584b38) dla bielik-minitron-7b-v3
   nie dotyczy zadan ani ewaluatora (diffy puste), ale **z danych na dysku nie wynika, czy poza
   `tasks/adversarial` i `src/polagentbench/eval` nie zmienilo sie nic wplywajacego na przebieg**
   (np. runner, prompty). Tego nie sprawdzalem -- zakres diffa byl narzucony.
6. Wszystkie liczby w tej sekcji dotycza wylacznie suite `main67` (67 zadan). Wyniki `ladder46`
   z katalogow-siostr nie sa tu uwzglednione.

---


<!-- source section: 08_bootstrap.md -->

## Podloga szumu: bootstrap CI 95% (resampling po zadaniach, 10 000 prob)

### 0. Metoda i prowenancja

- Skrypt zrodlowy: `analysis/bootstrap_ci.py` (nowy, TYLKO ODCZYT).
  Uruchomienie: `.venv/Scripts/python.exe analysis/bootstrap_ci.py` z katalogu glownego repo.
- Procedura: bootstrap **percentylowy**, przedzial **95%** (alpha = 0.05), resampling
  **po zadaniach** -- jedna obserwacja = jedno zadanie, wektor 0/1 dlugosci n = 67,
  losowanie ze zwracaniem, **10 000 prob** na komorke.
- Ziarno na sztywno: **SEED = 20260823**. `random.Random(SEED)` jest tworzony osobno dla kazdej
  komorki (wynik nie zalezy od kolejnosci komorek), wektor jest uporzadkowany rosnaco po `task_id`.
  Implementacja resamplingu: `polagentbench.eval.stats.bootstrap_ci(..., rng_seed=SEED)`.
  Odtwarzalnosc sprawdzona **trzema przebiegami** -- wyjscia identyczne bajt w bajt
  (md5 `10196f984a8105b80d926fdcb613e38d` dla przebiegow 2 i 3).
- Werdykt = **oracle**, nigdy `trajectory.success`:
  * `run.log` tam, gdzie plik istnieje: `results/v3_7b_grid_2026-07-29/q{5,6}_no_repair`
    oraz wszystkie 6 komorek `results/v3_pllum_2026-07-29/q{2,3,4,5,6,8}_main_no_repair`
    (8 z 18 komorek);
  * odtworzenie kodem repo przez `polagentbench.eval.smoke.evaluate` tam, gdzie `run.log` nie ma:
    `results/v3_11b_2026-06-18/q{2,3,4,5,6,8}_no_repair` (commit `a023c3b`) oraz
    `results/v3_arith_clean_2026-06-18/q{2,3,4,8}_no_repair` (commit `83db813`) -- 10 z 18 komorek.
    Legalne, bo `git diff --stat <commit> HEAD -- tasks/adversarial src/polagentbench/eval`
    jest pusty dla `a023c3b`, `83db813` i `e584b38`.
- Walidacja obowiazkowa dla kazdej komorki: `len(wektor) == 67` **oraz**
  `sum(wektor) == summary.json:num_passed`.
  Wynik uruchomienia 2026-08-23: **0 rozjazdow na 36 komorek** (18 repair=off + 18 repair=ON).
- Rozdzielczosc przedzialow wynosi 1/67 = 0.0149, bo srednia kazdej proby bootstrapowej jest
  postaci k/67 (np. szerokosc 0.239 = 16/67, szerokosc 0.104 = 7/67).

---

### 1. TABELA CI -- repair=off (krzywa glowna)

Zrodlo: `analysis/bootstrap_ci.py`, sekcja "TABELA CI -- repair=off".
Pliki wejsciowe: `run.log` / `trajectories.jsonl` + `summary.json` w katalogach wymienionych
w kolumnie "katalog".

| Model | Kwant | pass | n | rate | CI_low | CI_high | szer. CI | Zrodlo werdyktow | Katalog |
|---|---|---|---|---|---|---|---|---|---|
| bielik-11b-v3 | Q2_K   | 3  | 67 | 0.045 | 0.000 | 0.104 | 0.104 | odtworzone (eval.smoke) | `results/v3_11b_2026-06-18/q2_no_repair` |
| bielik-11b-v3 | Q3_K_M | 48 | 67 | 0.716 | 0.597 | 0.821 | 0.224 | odtworzone (eval.smoke) | `results/v3_11b_2026-06-18/q3_no_repair` |
| bielik-11b-v3 | Q4_K_M | 36 | 67 | 0.537 | 0.418 | 0.657 | 0.239 | odtworzone (eval.smoke) | `results/v3_11b_2026-06-18/q4_no_repair` |
| bielik-11b-v3 | Q5_K_M | 50 | 67 | 0.746 | 0.642 | 0.851 | 0.209 | odtworzone (eval.smoke) | `results/v3_11b_2026-06-18/q5_no_repair` |
| bielik-11b-v3 | Q6_K   | 56 | 67 | 0.836 | 0.746 | 0.925 | 0.179 | odtworzone (eval.smoke) | `results/v3_11b_2026-06-18/q6_no_repair` |
| bielik-11b-v3 | Q8_0   | 54 | 67 | 0.806 | 0.701 | 0.896 | 0.194 | odtworzone (eval.smoke) | `results/v3_11b_2026-06-18/q8_no_repair` |
| bielik-minitron-7b-v3 | Q2_K   | 10 | 67 | 0.149 | 0.075 | 0.239 | 0.164 | odtworzone (eval.smoke) | `results/v3_arith_clean_2026-06-18/q2_no_repair` |
| bielik-minitron-7b-v3 | Q3_K_M | 31 | 67 | 0.463 | 0.343 | 0.582 | 0.239 | odtworzone (eval.smoke) | `results/v3_arith_clean_2026-06-18/q3_no_repair` |
| bielik-minitron-7b-v3 | Q4_K_M | 34 | 67 | 0.507 | 0.388 | 0.627 | 0.239 | odtworzone (eval.smoke) | `results/v3_arith_clean_2026-06-18/q4_no_repair` |
| bielik-minitron-7b-v3 | Q5_K_M | 35 | 67 | 0.522 | 0.403 | 0.642 | 0.239 | run.log | `results/v3_7b_grid_2026-07-29/q5_no_repair` |
| bielik-minitron-7b-v3 | Q6_K   | 31 | 67 | 0.463 | 0.343 | 0.582 | 0.239 | run.log | `results/v3_7b_grid_2026-07-29/q6_no_repair` |
| bielik-minitron-7b-v3 | Q8_0   | 30 | 67 | 0.448 | 0.328 | 0.567 | 0.239 | odtworzone (eval.smoke) | `results/v3_arith_clean_2026-06-18/q8_no_repair` |
| llama-pllum-8b | Q2_K   | 1  | 67 | 0.015 | 0.000 | 0.045 | 0.045 | run.log | `results/v3_pllum_2026-07-29/q2_main_no_repair` |
| llama-pllum-8b | Q3_K_M | 15 | 67 | 0.224 | 0.134 | 0.328 | 0.194 | run.log | `results/v3_pllum_2026-07-29/q3_main_no_repair` |
| llama-pllum-8b | Q4_K_M | 15 | 67 | 0.224 | 0.134 | 0.328 | 0.194 | run.log | `results/v3_pllum_2026-07-29/q4_main_no_repair` |
| llama-pllum-8b | Q5_K_M | 7  | 67 | 0.104 | 0.030 | 0.179 | 0.149 | run.log | `results/v3_pllum_2026-07-29/q5_main_no_repair` |
| llama-pllum-8b | Q6_K   | 12 | 67 | 0.179 | 0.090 | 0.269 | 0.179 | run.log | `results/v3_pllum_2026-07-29/q6_main_no_repair` |
| llama-pllum-8b | Q8_0   | 13 | 67 | 0.194 | 0.104 | 0.284 | 0.179 | run.log | `results/v3_pllum_2026-07-29/q8_main_no_repair` |

---

### 2. TABELA CI -- repair=ON (dodatkowa)

Zrodlo: `analysis/bootstrap_ci.py`, sekcja "TABELA CI -- repair=ON".
Pliki wejsciowe: te same katalogi z sufiksem `_repair` / `_main_repair`.

| Model | Kwant | pass | n | rate | CI_low | CI_high | szer. CI | Zrodlo werdyktow |
|---|---|---|---|---|---|---|---|---|
| bielik-11b-v3 | Q2_K   | 5  | 67 | 0.075 | 0.015 | 0.149 | 0.134 | odtworzone (eval.smoke) |
| bielik-11b-v3 | Q3_K_M | 48 | 67 | 0.716 | 0.597 | 0.821 | 0.224 | odtworzone (eval.smoke) |
| bielik-11b-v3 | Q4_K_M | 40 | 67 | 0.597 | 0.478 | 0.716 | 0.239 | odtworzone (eval.smoke) |
| bielik-11b-v3 | Q5_K_M | 51 | 67 | 0.761 | 0.657 | 0.866 | 0.209 | odtworzone (eval.smoke) |
| bielik-11b-v3 | Q6_K   | 57 | 67 | 0.851 | 0.761 | 0.925 | 0.164 | odtworzone (eval.smoke) |
| bielik-11b-v3 | Q8_0   | 54 | 67 | 0.806 | 0.701 | 0.896 | 0.194 | odtworzone (eval.smoke) |
| bielik-minitron-7b-v3 | Q2_K   | 12 | 67 | 0.179 | 0.090 | 0.284 | 0.194 | odtworzone (eval.smoke) |
| bielik-minitron-7b-v3 | Q3_K_M | 31 | 67 | 0.463 | 0.343 | 0.582 | 0.239 | odtworzone (eval.smoke) |
| bielik-minitron-7b-v3 | Q4_K_M | 40 | 67 | 0.597 | 0.478 | 0.716 | 0.239 | odtworzone (eval.smoke) |
| bielik-minitron-7b-v3 | Q5_K_M | 40 | 67 | 0.597 | 0.478 | 0.716 | 0.239 | run.log |
| bielik-minitron-7b-v3 | Q6_K   | 38 | 67 | 0.567 | 0.448 | 0.687 | 0.239 | run.log |
| bielik-minitron-7b-v3 | Q8_0   | 38 | 67 | 0.567 | 0.448 | 0.687 | 0.239 | odtworzone (eval.smoke) |
| llama-pllum-8b | Q2_K   | 1  | 67 | 0.015 | 0.000 | 0.045 | 0.045 | run.log |
| llama-pllum-8b | Q3_K_M | 18 | 67 | 0.269 | 0.164 | 0.373 | 0.209 | run.log |
| llama-pllum-8b | Q4_K_M | 17 | 67 | 0.254 | 0.149 | 0.358 | 0.209 | run.log |
| llama-pllum-8b | Q5_K_M | 9  | 67 | 0.134 | 0.060 | 0.224 | 0.164 | run.log |
| llama-pllum-8b | Q6_K   | 14 | 67 | 0.209 | 0.119 | 0.313 | 0.194 | run.log |
| llama-pllum-8b | Q8_0   | 15 | 67 | 0.224 | 0.134 | 0.328 | 0.194 | run.log |

---

### 3. Porownanie (a): czy przedzialy Q8, Q6, Q5 nachodza na siebie

Zrodlo: `analysis/bootstrap_ci.py`, blok "(a)". Liczone na repair=off.

| Model | Para | CI pierwszego | CI drugiego | Roznica rate | Czesc wspolna | Szer. czesci wspolnej |
|---|---|---|---|---|---|---|
| bielik-11b-v3 | Q8_0 vs Q6_K   | [0.701, 0.896] | [0.746, 0.925] | -0.030 | [0.746, 0.896] | 0.149 |
| bielik-11b-v3 | Q8_0 vs Q5_K_M | [0.701, 0.896] | [0.642, 0.851] | +0.060 | [0.701, 0.851] | 0.149 |
| bielik-11b-v3 | Q6_K vs Q5_K_M | [0.746, 0.925] | [0.642, 0.851] | +0.090 | [0.746, 0.851] | 0.104 |
| bielik-minitron-7b-v3 | Q8_0 vs Q6_K   | [0.328, 0.567] | [0.343, 0.582] | -0.015 | [0.343, 0.567] | 0.224 |
| bielik-minitron-7b-v3 | Q8_0 vs Q5_K_M | [0.328, 0.567] | [0.403, 0.642] | -0.075 | [0.403, 0.567] | 0.164 |
| bielik-minitron-7b-v3 | Q6_K vs Q5_K_M | [0.343, 0.582] | [0.403, 0.642] | -0.060 | [0.403, 0.582] | 0.179 |
| llama-pllum-8b | Q8_0 vs Q6_K   | [0.104, 0.284] | [0.090, 0.269] | +0.015 | [0.104, 0.269] | 0.164 |
| llama-pllum-8b | Q8_0 vs Q5_K_M | [0.104, 0.284] | [0.030, 0.179] | +0.090 | [0.104, 0.179] | 0.075 |
| llama-pllum-8b | Q6_K vs Q5_K_M | [0.090, 0.269] | [0.030, 0.179] | +0.075 | [0.090, 0.179] | 0.090 |

Wszystkie 9 par nachodza na siebie. Czesc wspolna calej trojki Q8/Q6/Q5:
bielik-11b-v3 **[0.746, 0.851]** (szer. 0.104), bielik-minitron-7b-v3 **[0.403, 0.567]**
(szer. 0.164), llama-pllum-8b **[0.104, 0.179]** (szer. 0.075).

---

### 4. Porownanie (b): spadek Q3 -> Q2 wobec szerokosci CI

Zrodlo: `analysis/bootstrap_ci.py`, blok "(b)". Liczone na repair=off.
"Szerszy" = szerszy z dwoch przedzialow (Q3 albo Q2), w punktach procentowych.

| Model | rate Q3 | rate Q2 | Spadek [pp] | Szer. CI Q3 [pp] | Szer. CI Q2 [pp] | Szerszy [pp] | Nadwyzka [pp] | Krotnosc |
|---|---|---|---|---|---|---|---|---|
| bielik-11b-v3 | 0.716 | 0.045 | 67.2 | 22.4 | 10.4 | 22.4 | **+44.8** | 3.00x |
| bielik-minitron-7b-v3 | 0.463 | 0.149 | 31.3 | 23.9 | 16.4 | 23.9 | **+7.5** | 1.31x |
| llama-pllum-8b | 0.224 | 0.015 | 20.9 | 19.4 | 4.5 | 19.4 | **+1.5** | 1.08x |

W kazdym z trzech modeli przedzialy Q3 i Q2 sa **rozlaczne**:
bielik-11b-v3 [0.597, 0.821] vs [0.000, 0.104], bielik-minitron-7b-v3 [0.343, 0.582] vs
[0.075, 0.239], llama-pllum-8b [0.134, 0.328] vs [0.000, 0.045].

---

### 5. Zdanie podsumowania

Roznice miedzy Q8, Q6 i Q5 mieszcza sie w przedzialach ufnosci u wszystkich trzech modeli
(kazda z 9 par ma niepusta czesc wspolna, a cala trojka dzieli przedzial [0.746, 0.851] na
bielik-11b-v3, [0.403, 0.567] na bielik-minitron-7b-v3 i [0.104, 0.179] na llama-pllum-8b),
natomiast spadek Q3 -> Q2 przekracza szerokosc szerszego z dwoch CI o 44.8 pp na bielik-11b-v3
(67.2 pp wobec 22.4 pp, 3.00x), o 7.5 pp na bielik-minitron-7b-v3 (31.3 pp wobec 23.9 pp, 1.31x)
i o 1.5 pp na llama-pllum-8b (20.9 pp wobec 19.4 pp, 1.08x).

---


<!-- source section: 04_q4dip_envelope.md -->

# Dip Q4 i envelope collapse

Wszystkie liczby ponizej pochodza z gotowych wyjsc skryptow `analysis/*.py`, zapisanych w
`scratchpad\analysis_out\<nazwa>.txt`. Zadnego runu modelu nie powtarzano; zadnego GPU nie uzyto.

---

## Dip Q4 (Bielik-11B, main67)

Wszystkie komorki tej czesci: model `bielik-11b-v3`, suita `main67` (67 zadan z `tasks/adversarial/*.yaml`),
repair **off**, katalog `results/v3_11b_2026-06-18/{q3,q4,q5}_no_repair`, commit runu `a023c3b`.
Katalog czerwcowy **nie ma `run.log`**, wiec werdykty odtworzono kodem HEAD
(`src/polagentbench/eval/smoke.py::evaluate`). Jest to legalne, bo
`git diff --stat a023c3b HEAD -- tasks/adversarial src/polagentbench/eval` jest pusty.
`trajectory.success` nie byl uzyty nigdzie w tej sekcji.

### A.1 Walidacja odtworzenia oracle

Skrypt: `analysis/q4dip_classify.py` -> `analysis_out/q4dip_classify.txt`, blok
"WALIDACJA odtworzonego oracle wobec summary.json i per_task_matrix.csv".
Wejscie: `results/v3_11b_2026-06-18/{q3,q4,q5}_no_repair/{trajectories.jsonl,summary.json}` +
`results/v3_11b_2026-06-18/analysis/per_task_matrix.csv` + `tasks/adversarial/*.yaml`.

| kwant | odtworzone PASS | `summary.json` num_passed | zgodnosc | rozjazdow z `per_task_matrix.csv` |
|---|---|---|---|---|
| Q3_K_M | 48 | 48 | ZGODNE | 0 |
| Q4_K_M | 36 | 36 | ZGODNE | 0 |
| Q5_K_M | 50 | 50 | ZGODNE | 0 |

Zadan zaladowanych z `tasks/adversarial`: 67 (pierwsza linia `q4dip_classify.txt`).
Liczba rozjazdow **0** w kazdym z trzech kwantow, wobec obu niezaleznych zrodel odniesienia.

### A.2 Klasyfikacja porazek A/B/C i sufity

Skrypt: `analysis/q4dip_classify.py` -> `q4dip_classify.txt`, "TABELA 1a". Wejscie jak wyzej.

Definicje z kodu (`q4dip_classify.py`, zbiory `FORMAT` / `CONTENT`):
A = tylko tagi formatowe; B = tagi formatowe **i** trescowe (kaskada mozliwa); C = tylko tagi trescowe.
Sufit ostrozny = PASS + A. Sufit hojny = PASS + A + B.

| kwant | PASS | porazek | A format | B kaskada | C tresc | sufit ostrozny | sufit hojny |
|---|---|---|---|---|---|---|---|
| Q3_K_M | 48/67 | 19 | 5 | 4 | 10 | 53/67 = 0.791 | 57/67 = 0.851 |
| Q4_K_M | 36/67 | 31 | 3 | **16** | 12 | 39/67 = 0.582 | 55/67 = 0.821 |
| Q5_K_M | 50/67 | 17 | 2 | 9 | 6 | 52/67 = 0.776 | 61/67 = 0.910 |

Zgodnosc wewnetrzna: 48+19=67, 36+31=67, 50+17=67; 5+4+10=19, 3+16+12=31, 2+9+6=17.

### A.3 Liczba kluczowa: dip Q4 vs Q5

Skrypt: `analysis/q4dip_classify.py` -> `q4dip_classify.txt`, blok
"PYTANIE ROZSTRZYGAJACE: czy dip Q4 przezywa darowanie kaskad?". Sa tam dokladnie trzy wiersze:

| wiersz w pliku | Q3 | Q4 | Q5 | dip Q4 vs Q5 | dip Q4 vs Q3 |
|---|---|---|---|---|---|
| `scisle` | 48/67 (0.716) | 36/67 (0.537) | 50/67 (0.746) | **-0.209** | -0.179 |
| `po darowaniu A` | 53/67 (0.791) | 39/67 (0.582) | 52/67 (0.776) | -0.194 | -0.209 |
| `po darowaniu A+B` | 57/67 (0.851) | 55/67 (0.821) | 61/67 (0.910) | **-0.090** | -0.030 |

**POTWIERDZENIE obu liczb:**
- **-0.209** pochodzi z wiersza oznaczonego w pliku `scisle` (3. wiersz bloku, kolumna `dip Q4 vs Q5`).
  Kontrola arytmetyczna: 36/67 - 50/67 = 0.53731 - 0.74627 = -0.20896.
- **-0.090** pochodzi z wiersza oznaczonego w pliku `po darowaniu A+B` (5. wiersz bloku, ta sama kolumna).
  Kontrola arytmetyczna: 55/67 - 61/67 = 0.82090 - 0.91045 = -0.08955.

Uwaga na jeden efekt uboczny widoczny w tabeli: po darowaniu samego A dip wobec **Q3** rosnie
(-0.179 -> -0.209), bo Q3 ma 5 porazek klasy A wobec 3 na Q4.

### A.4 Rozbicie na glebokosc lancucha

Skrypt: `analysis/q4dip_depth.py` -> `analysis_out/q4dip_depth.txt`, "TABELA 1c".
Wejscie: jak w `q4dip_classify.py` (docstring `q4dip_depth.py`: "CZYTA Z: jak w q4dip_classify.py").
Kubelek = dlugosc oczekiwanego lancucha wywolan zapisana w zadaniu.

| glebokosc | n | Q3_K_M | Q4_K_M | Q5_K_M | Q4-Q5 | Q4-Q3 |
|---|---|---|---|---|---|---|
| 0-1 wywolan | 8 | 5/8 (0.62) | 1/8 (0.12) | 3/8 (0.38) | -0.25 | -0.50 |
| 2-3 wywolania | 25 | 17/25 (0.68) | 19/25 (0.76) | 18/25 (0.72) | **+0.04** | **+0.08** |
| 4+ wywolan | 25 | 17/25 (0.68) | **8/25 (0.32)** | **21/25 (0.84)** | **-0.52** | -0.36 |
| brak checku | 9 | 9/9 (1.00) | 8/9 (0.89) | 8/9 (0.89) | +0.00 | -0.11 |

8+25+25+9 = 67. W kubelku **4+ wywolan** Q4 daje **0.32** wobec **0.84** na Q5 (roznica -0.52).
W kubelku **2-3 wywolania** Q4 jest **wyzej** i od Q5 (+0.04), i od Q3 (+0.08).

Zuzycie krokow, cala suita (ten sam plik, "TABELA 1d"):

| kwant | krokow | krokow/traj | traj. na max_steps | traj. z timeout |
|---|---|---|---|---|
| Q3_K_M | 299 | 4.46 | 8 | 3 |
| Q4_K_M | 313 | 4.67 | 14 | 14 |
| Q5_K_M | 310 | 4.63 | 7 | 6 |

Tylko zadania o glebokosci 4+ (ten sam plik, "TABELA 1e"):

| kwant | PASS | sr. krokow | na max_steps | udanych call_tool | unknown_action | no_json |
|---|---|---|---|---|---|---|
| Q3_K_M | 17/25 | 6.28 | 6 | 123 | 12 | 0 |
| Q4_K_M | 8/25 | 6.04 | 8 | **87** | **45** | 1 |
| Q5_K_M | 21/25 | 6.36 | 3 | 127 | 4 | 0 |

Sufity wewnatrz kubelka 4+ — skrypt `analysis/q4dip_deep_ceiling.py` -> `analysis_out/q4dip_deep_ceiling.txt`
(naglowek pliku: "zadan o glebokosci >=4: 25"):

| kwant | PASS | A | B | C | sufit ostrozny | sufit hojny |
|---|---|---|---|---|---|---|
| Q3_K_M | 17/25 | 0 | 4 | 4 | 17/25 = 0.680 | 21/25 = 0.840 |
| Q4_K_M | 8/25 | 0 | 9 | 8 | 8/25 = 0.320 | 17/25 = 0.680 |
| Q5_K_M | 21/25 | 0 | 4 | 0 | 21/25 = 0.840 | 25/25 = 1.000 |

Dip w kubelku 4+: scisle -0.520, po darowaniu A -0.520 (A=0 we wszystkich trzech kwantach),
po darowaniu A+B **-0.320** (wobec Q3: -0.160).

### A.5 Grupa 14 zadan padajacych tylko na Q4

Skrypt: `analysis/q4dip_group.py` -> `analysis_out/q4dip_group.txt`, "TABELA 1b".
Kryterium: PASS na Q5 **i** Q3, FAIL na Q4. Liczebnosc: **14 z 67**.

| task_id | rodzina | n wywolan | klasa | tagi Q4 |
|---|---|---|---|---|
| adv_010 | adv | 0 | B | final_answer_missing, timeout, unknown_action |
| v3_arith_L1_c | v3_arith | 1 | B | final_answer_missing, schema_violation, timeout |
| v3_arith_L3_b | v3_arith | 4 | B | final_answer_missing, timeout, unknown_action, wrong_tool_order |
| v3_arith_L3_c | v3_arith | 4 | C | wrong_final_answer, wrong_tool_order |
| v3_chain_001 | v3_chain | 4 | B | final_answer_missing, timeout, unknown_action, wrong_tool_order |
| v3_chain_002 | v3_chain | 4 | B | final_answer_missing, timeout, unknown_action, wrong_tool_order |
| v3_chain_004 | v3_chain | 4 | B | final_answer_missing, timeout, unknown_action, wrong_tool_order |
| v3_chain_005 | v3_chain | 4 | C | wrong_tool_order |
| v3_chain_005_arith | v3_chain | 4 | C | wrong_final_answer, wrong_tool_order |
| v3_chain_007 | v3_chain | 4 | B | final_answer_missing, timeout, unknown_action, wrong_tool_order |
| v3_chain_007_arith | v3_chain | 4 | B | final_answer_missing, timeout, unknown_action, wrong_tool_order |
| v3_chain_009 | v3_chain | 5 | C | wrong_tool_order |
| v3_chain_en_001 | v3_chain | 3 | A | invalid_json |
| v3_chain_en_007 | v3_chain | 5 | C | wrong_tool_order |

Rozklad klas w grupie: **B=8, C=5, A=1**.
Zliczenia tagow w grupie: `wrong_tool_order` 11, `final_answer_missing` 8, `timeout` 8,
`unknown_action` 7, `wrong_final_answer` 2, `schema_violation` 1, `invalid_json` 1.

Wzbogacenia grupy wobec calej suity (ten sam plik, blok "czy to spojna grupa?"):

| cecha | grupa (n=14) | suita (n=67) |
|---|---|---|
| lancuch >= 4 wywolan | 4 wyw. 9 (64%) + 5 wyw. 2 (14%) = **11/14 = 79%** | 4 wyw. 15 (22%) + 5 wyw. 9 (13%) + 6 wyw. 1 (1%) = **25/67 = 37%** |
| wymaga `convert_temperature` | **12/14 = 86%** | **44/67 = 66%** |
| pierwsze narzedzie `get_weather` | 12 (86%) | 48 (72%) |
| rodzina `v3_chain` | 10 (71%) | 40 (60%) |
| rodzina `v3_arith` | 3 (21%) | 12 (18%) |
| rodzina `adv` | 1 (7%) | 15 (22%) |

Odsetki 79% i 37% sa wyliczone z rozbicia w pliku (79% = 11/14 = 0.7857; 37% = 25/67 = 0.3731);
sam plik podaje skladniki (64%+14% oraz 22%+13%+1%), nie sume.

**Identyczna sygnatura tagow:** dokladnie **6 z 14** zadan ma ten sam czteroelementowy zbior
`{final_answer_missing, timeout, unknown_action, wrong_tool_order}`:
`v3_arith_L3_b`, `v3_chain_001`, `v3_chain_002`, `v3_chain_004`, `v3_chain_007`, `v3_chain_007_arith`
(policzone z kolumny "tagi Q4" TABELI 1b powyzej).

**Kontrola odwrotna** (ten sam plik, ostatni blok): zadan FAIL na Q5 i Q3 przy PASS na Q4 jest
**1**: `adv_004b`.

### A.6 Ograniczenia czesci A

- Sufit hojny darowuje **cala** klase B, wiec jest gorna granica przy zalozeniu, ze kazdy blad
  formatu w kaskadzie byl przyczyna, a nie skutkiem. Sufit ostrozny darowuje tylko A.
- Skrypty czesci A pokrywaja **tylko Q3/Q4/Q5**. Analogicznej klasyfikacji A/B/C dla Q2/Q6/Q8
  na Bielik-11B w moich zrodlach **BRAK DANYCH** (jedyne dostepne A/B/C dla Q8 jest w
  `pllum_ceiling.txt`: Bielik-11B Q8_0 PASS=54/67, A=6, B=3, C=4, sufit ostrozny 60/67=0.896,
  sufit hojny 63/67=0.940).
- Przedzialy ufnosci / testy istotnosci dla dipu: **BRAK DANYCH** — zaden ze skryptow zrodlowych
  ich nie liczy. Kazda komorka to jeden przebieg (seed i temperatura nie sa w `summary.json`).
- `n` w TABELI 1b to dlugosc **oczekiwanego** lancucha zapisana w zadaniu, nie liczba wywolan
  faktycznie wykonanych przez model.

---

## Envelope collapse

Splaszczona koperta = krok, w ktorym `parse_error.category == "unknown_action"`, tj. model
napisal nazwe narzedzia wprost w polu `action` zamiast koperty `{"action":"call_tool","tool":...}`
(definicja z kodu `analysis/envelope_positions.py`, funkcje `flat_name` i filtr `flat`).

### B.1 Ktore runy maja dokladnie 18 splaszczonych kopert

Skrypt: `analysis/inventory.py` -> `analysis_out/inventory.txt`, ostatni blok pliku
"=== runy z DOKLADNIE 18 splaszczonymi kopertami (unknown_action) ===".
Wejscie: `results/**/summary.json` + `results/**/trajectories.jsonl` (112 wierszy tabeli inwentarza).

Takie runy sa **dwa**, nie jeden:

| model | kwant | suita | repair | wynik | unknown_action | krokow | run.log | commit | katalog |
|---|---|---|---|---|---|---|---|---|---|
| bielik-minitron-7b-v3 | Q5_K_M | 45 (num_total=45) | off | 24/45 | **18** | 213 | BRAK | d6088b3 | `results\v3_full_2026-06-02\Q5_K_M` |
| llama-pllum-8b | Q8_0 | main67 | off | 13/67 | **18** | 174 | TAK | e584b38 | `results\v3_pllum_2026-07-29\q8_main_no_repair` |

Wiersze zrodlowe: `inventory.txt` linie 36 i 114 (tabela) oraz linie 117-118 (blok podsumowania).

Doprecyzowanie: na suicie **main67** run z dokladnie 18 splaszczeniami jest **jeden** —
PLLuM-8B Q8_0 repair=off. Drugi run z 18 lezy na innej, 45-zadaniowej suicie
(`results/v3_full_2026-06-02`, commit `d6088b3` — commit, na ktorym odtwarzanie werdyktow kodem
HEAD jest **nielegalne**; tu jednak nic nie odtwarzano, liczba `unknown_action` jest odczytana
wprost z zapisanych `parse_error` w `trajectories.jsonl`). Cala dalsza analiza envelope dotyczy
runu PLLuM main67.

Dla porownania oba runy Bielika-7B Q8 na main67 maja odpowiednio **31** i **50** splaszczen
(`inventory.txt` linie 84 i 85), a wariant PLLuM Q8 z repair=ON ma **10** (`inventory.txt` linia 113).

Rozbieznosc do odnotowania: docstring `analysis/inventory.py` mowi o "tabeli inwentarza 120 runow"
i o "jedynym runie", a wypis zawiera **112** wierszy i **dwa** runy z 18.

### B.2 Lista 18 splaszczen w runie PLLuM-8B Q8_0 main67 (repair=off)

Skrypt: `analysis/envelope_positions.py` -> `analysis_out/envelope_positions.txt`, pierwszy blok.
Wejscie: `results/v3_pllum_2026-07-29/q8_main_no_repair/trajectories.jsonl`.
Naglowek bloku: trajektorii=67, krokow=174, splaszczonych kopert=18.

| # | zadanie | krok (1-idx) | nazwa w polu `action` | poz. w lancuchu |
|---|---|---|---|---|
| 1 | adv_001 | 1 | send_weather_alert | 1 |
| 2 | adv_006 | 2 | send_weather_alert | 2 |
| 3 | adv_008 | 2 | send_weather_alert | 2 |
| 4 | adv_009b | 1 | send_weather_alert | 1 |
| 5 | adv_012 | 2 | send_weather_alert | 2 |
| 6 | v3_arith_L3_c | 4 | convert_temperature | 4 |
| 7 | v3_arith_L3_c | 5 | convert_temperature | 4 |
| 8 | v3_chain_005 | 4 | convert_temperature | 4 |
| 9 | v3_chain_005 | 5 | convert_temperature | 4 |
| 10 | v3_chain_005_arith | 4 | convert_temperature | 4 |
| 11 | v3_chain_005_arith | 5 | convert_temperature | 4 |
| 12 | v3_chain_en_004 | 2 | (brak pola action) | 2 |
| 13 | v3_chain_en_004 | 4 | (brak pola action) | 3 |
| 14 | v3_chain_en_004_arith | 2 | (brak pola action) | 2 |
| 15 | v3_chain_en_004_arith | 4 | (brak pola action) | 3 |
| 16 | v3_chain_en_005 | 3 | convert_temperature | 3 |
| 17 | v3_chain_en_006 | 3 | convert_temperature | 3 |
| 18 | v3_chain_en_007 | 2 | (brak pola action) | 2 |

Rozklad nazw: `convert_temperature` 8, `send_weather_alert` 5, brak pola `action` 5
(zgodne z `analysis_out/pllum_patterns.txt`, blok "unknown_action (18 krokow)": 8 / 5 / 5).

Piec przypadkow "brak pola action" to — wedlug `analysis_out/envelope_marginals.txt`, pierwszy blok —
gole obiekty `{"answer": ...}` bez koperty (4 razy tekst "Przepraszam, nie udalo mi sie sprawdzic
pogody w Madrycie...", raz zdanie o temperaturach w Atenach), a nie proby wywolania `convert`.

Tlo runu (`analysis_out/pllum_patterns.txt`): 174 kroki, sparsowanych poprawnie 146 (83.9%),
blednych 28 (16.1%) w rozbiciu `unknown_action` 18, `no_json_found` 9, `invalid_json` 1.

### B.3 Ilorazy ryzyka: narzedzie wobec pozycji

Skrypt: `analysis/envelope_marginals.py` -> `analysis_out/envelope_marginals.txt`,
blok "### PLLuM-8B Q8 main   krokow=174  bledow parsowania=28".
Wejscie: `results/v3_pllum_2026-07-29/q8_main_no_repair/trajectories.jsonl`.
"Zla koperta" w tym bloku = `parse_error is not None` (wszystkie 28 bledow parsowania, nie tylko 18 splaszczen).

| warunek | zlych / wszystkich | udzial zlych |
|---|---|---|
| narzedzie = `convert_temperature` | **8/16** | 50.0% |
| narzedzie != `convert_temperature` | **20/158** | 12.7% |
| -> iloraz ryzyka (narzedzie) | | **3.95x** |
| pozycja = trzeci krok | **3/29** | 10.3% |
| pozycja != trzeci krok | **25/145** | 17.2% |
| -> iloraz ryzyka (pozycja) | | **0.60x** |

**POTWIERDZENIE surowych licznikow z SESSION_LOG:** obie pary zgadzaja sie z plikiem.
- "16/158" = mianowniki wiersza narzedzia: 16 krokow z `convert_temperature`, 158 pozostalych;
  16+158 = 174 = liczba krokow runu.
- "29/145" = mianowniki wiersza pozycji: 29 krokow trzecich, 145 pozostalych; 29+145 = 174.
- Liczniki (zle koperty) to odpowiednio 8 i 20 oraz 3 i 25; 8+20 = 3+25 = 28 = liczba bledow parsowania.
- Kontrola ilorazow: (8/16)/(20/158) = 0.5000/0.12658 = 3.950; (3/29)/(25/145) = 0.10345/0.17241 = 0.600.

Kierunek: iloraz narzedzia > 1 (3.95x), iloraz pozycji < 1 (0.60x) — trzeci krok ma **nizszy**
udzial zlych kopert niz reszta krokow tego runu.

### B.4 Rozdzielenie zmiennych (pozycja kontra narzedzie)

Skrypt: `analysis/envelope_positions.py` -> `analysis_out/envelope_positions.txt`,
punkty (a)/(b)/(c) i tabela 2x2 w bloku PLLuM. Definicje z kodu: `is_conv` = krok, w ktorym
narzedziem jest `convert_temperature` (z poprawnie sparsowanej koperty albo z nazwy w splaszczonym
polu `action`); `ok_env` = `parse_error is None`; trzeci krok = `step_idx == 2`.

- (a) krokow trzecich w runie: **29**, z nich `convert_temperature`: **2** (6.9%).
- (b) wywolan `convert_temperature` **poza** trzecim krokiem: **14** — z poprawna koperta **8**,
  ze splaszczona **6**.
- (c) krokow trzecich **bez** `convert`: **27** — z poprawna koperta **26**, ze splaszczona/bledna **1**.

Obie komorki (b) i (c) sa niepuste, wiec zmienne "pozycja = trzeci krok" i
"narzedzie = convert_temperature" **nie sa w tym runie calkowicie skonfundowane**:
`convert` wystepuje 14 razy poza trzecim krokiem i trzeci krok wystepuje 27 razy bez `convert`.

Tabela 2x2 (ten sam plik):

| komorka | koperta OK | koperta zla | razem | udzial zlych |
|---|---|---|---|---|
| trzeci krok + `convert` | 0 | 2 | **2** | 100.0% |
| trzeci krok, bez `convert` | 26 | 1 | 27 | 3.7% |
| `convert` poza 3. krokiem | 8 | 6 | 14 | 42.9% |
| reszta krokow | 112 | 19 | 131 | 14.5% |

Sumy kontrolne: 2+27+14+131 = 174 kroki; 2+1+6+19 = 28 zlych kopert; kolumna `convert`
(2 + 14 = 16) i kolumna "trzeci krok" (2 + 27 = 29) zgadzaja sie z mianownikami z B.3.

### B.5 Kontrast: Bielik-7B Q8_0, te same dwie zmienne

Skrypt: `analysis/envelope_marginals.py` -> `analysis_out/envelope_marginals.txt`, bloki 2 i 3.
Wejscie: `results/v3_arith_clean_2026-06-18/q8_no_repair/trajectories.jsonl` (commit `83db813`)
oraz `results/v3_ladder_2026-06-11/q8_no_repair/trajectories.jsonl` (commit `ef122d4`).
Oba runy: `bielik-minitron-7b-v3`, Q8_0, main67, repair=off. Nic tu nie jest odtwarzane kodem HEAD —
czytane sa wylacznie zapisane pola `parse_error`, wiec commit `ef122d4` nie jest problemem.

| run | krokow | bledow parsowania | tlo (udzial zlych) | convert | nie-convert | iloraz (narzedzie) | 3. krok | nie-3. krok | iloraz (pozycja) |
|---|---|---|---|---|---|---|---|---|---|
| PLLuM-8B Q8 main67 | 174 | 28 | 16.1% | 8/16 = 50.0% | 20/158 = 12.7% | **3.95x** | 3/29 = 10.3% | 25/145 = 17.2% | **0.60x** |
| Bielik-7B Q8 (arith_clean) | 368 | 137 | 37.2% | 28/96 = 29.2% | 109/272 = 40.1% | **0.73x** | 18/58 = 31.0% | 119/310 = 38.4% | **0.81x** |
| Bielik-7B Q8 (ladder0611) | 371 | 141 | 38.0% | 47/114 = 41.2% | 94/257 = 36.6% | **1.13x** | 17/58 = 29.3% | 124/313 = 39.6% | **0.74x** |

Tlo (udzial zlych kopert w calym runie) policzone z naglowkow blokow: 28/174 = 16.1%,
137/368 = 37.2%, 141/371 = 38.0%. Osiem udzialow warunkowych obu runow Bielika-7B miesci sie
w przedziale **29.2%–41.2%**, czyli w pasmie 30–40% wokol tla; ilorazy narzedzia to 0.73x i 1.13x
(raz ponizej, raz powyzej jednosci), ilorazy pozycji 0.81x i 0.74x.

Liczby splaszczonych kopert (`unknown_action`, `envelope_positions.txt`, naglowki blokow 2 i 3
oraz `inventory.txt` linie 84-85): arith_clean **31**, ladder0611 **50** — przy 18 w runie PLLuM.

Tabele 2x2 dla Bielika-7B (`envelope_positions.txt`), dla porzadku:

| komorka | arith_clean OK / zla / razem / % | ladder0611 OK / zla / razem / % |
|---|---|---|
| trzeci krok + `convert` | 8 / 9 / 17 / 52.9% | 10 / 6 / 16 / 37.5% |
| trzeci krok, bez `convert` | 32 / 9 / 41 / 22.0% | 31 / 11 / 42 / 26.2% |
| `convert` poza 3. krokiem | 60 / 19 / 79 / 24.1% | 57 / 41 / 98 / 41.8% |
| reszta krokow | 131 / 100 / 231 / 43.3% | 132 / 83 / 215 / 38.6% |

### B.6 Ograniczenia czesci B

- **Liczebnosc komorki "trzeci krok + convert" w runie PLLuM wynosi 2** (0 poprawnych kopert,
  2 zle, `envelope_positions.txt`, tabela 2x2). Udzial 100.0% jest liczony z dwoch obserwacji;
  zmiana jednej z nich przesuwa go do 50%. Zadnych przedzialow ufnosci ani testu na tej tabeli
  nie policzono — **BRAK DANYCH**.
- Dwie rozne definicje "zlej koperty" wspolistnieja w zrodlach: `envelope_positions.py` liczy
  w naglowku **splaszczenia** (`unknown_action`, 18), a w tabeli 2x2 i w calym
  `envelope_marginals.py` "zla koperta" = **dowolny** `parse_error` (28). Stad 18 wobec 28
  w tym samym runie. Porownania w B.3–B.5 uzywaja konsekwentnie definicji szerszej (28).
- Zmienna "narzedzie = convert_temperature" jest dla krokow blednych odczytywana z tresci
  wyjscia modelu (`flat_name` czyta pole `"action"` z surowego tekstu). Krok, ktory splaszczyl
  koperte piszac `"action": "convert_temperature"`, jest wiec **z definicji** jednoczesnie
  "convert" i "zly". `envelope_marginals.py` dodatkowo zalicza do `convert` kroki bez pola
  `action`, w ktorych surowe wyjscie zawiera `"value"` i `"unit"` — w runie PLLuM zaden z 5
  takich krokow tego warunku nie spelnia, wiec mianownik 16 pozostaje taki sam w obu skryptach.
- Analiza envelope obejmuje **tylko kwant Q8_0** i trzy wymienione runy. Analogicznych ilorazow
  ryzyka dla Q2/Q3/Q4/Q5/Q6 (dowolnego modelu) w moich zrodlach **BRAK DANYCH**.
- Powiazanie splaszczen z werdyktem PASS/FAIL zadania (ile z 54 porazek PLLuM ma splaszczenie)
  nie jest liczone w plikach `envelope_*` — **BRAK DANYCH** w tej sekcji; osobno
  `analysis_out/pllum_ceiling.txt` podaje dla PLLuM-8B Q8_0: PASS=13/67, A=1, B=18, C=35,
  sufit ostrozny 14/67 = 0.209, sufit hojny 32/67 = 0.478.

---


<!-- source section: 02_drabina.md -->

## Drabina L0-L3N

Suite `ladder46` = `tasks/ladder_ext/*.yaml` = 46 plikow. Wszystkie liczby w tej sekcji pochodza
z 14 runow `repair OFF`, T=0, seed=42:

| model | katalog runow | kwanty | commit |
|---|---|---|---|
| bielik-11b-v3 | `results/v3_11b_ladder_2026-07-29/q{8,4,3,2}_no_repair` | Q8_0, Q4_K_M, Q3_K_M, Q2_K | e584b38 |
| bielik-minitron-7b-v3 | `results/v3_7b_ladder_2026-07-29/q{8,4,3,2}_no_repair` | Q8_0, Q4_K_M, Q3_K_M, Q2_K | e584b38 |
| llama-pllum-8b | `results/v3_pllum_2026-07-29/q{8,6,5,4,3,2}_ladder_no_repair` | Q8_0, Q6_K, Q5_K_M, Q4_K_M, Q3_K_M, Q2_K | e584b38 |

Wszystkie 14 runow drabiny pochodzi z jednego commita **e584b38** (pole `commit_hash` w
`summary.json` kazdego runu). `git diff --stat e584b38 HEAD -- tasks/ladder_ext src/polagentbench/eval`
jest **pusty**, wiec odtwarzanie werdyktow kodem HEAD jest legalne dla wszystkich komorek drabiny.
Werdykt kazdego zadania czytany jest ze znaku `✓`/`✗` w `run.log` (oracle), nigdy z
`trajectory.success`.

---

### 1. Definicje szczebli

Zrodlo: `analysis_out/ladder_rungs.txt` (skrypt `analysis/ladder_rungs.py`, czyta `tasks/ladder_ext/*.yaml`,
wypisuje pierwsza instancje kazdego szczebla).

| szczebel | check lancucha | wymagany lancuch narzedzi | wymaganych konwersji | komplet checkow z YAML | max_steps |
|---|---|---|---|---|---|
| L0 | **brak** (`no_tool_calls: true`) | brak lancucha — narzedzia ZABRONIONE | 0 | `final_answer_contains_any`, `final_answer_used`, `no_tool_calls` | 8 |
| L1 | `tools_called_in_order_strict` | `get_forecast` | 0 | `final_answer_contains_any`, `final_answer_used`, `tools_called_in_order_strict` | 8 |
| L2 | `tools_called_in_order_strict` | `get_weather > get_forecast` | 0 | jw. | 8 |
| L3N | `tools_called_in_order_strict` | `get_weather > get_forecast > convert_temperature > convert_temperature` | **2** | jw. | 8 |
| L3T | `tools_called_in_order_strict` | `get_weather > find_nearest_city > get_forecast > convert_temperature` | **1** | jw. | 8 |

Co dokladnie kazdy szczebel wymaga/zabrania (odczyt z YAML, `tasks/ladder_ext/v3_ext_*_a.yaml`):

- **L0** — jedyny szczebel, ktory czegos ZABRANIA. `no_tool_calls: true`: dane sa juz w promptcie
  (`"Oto prognoza temperatury na 4 dni: 7, 7.5, 8, 8.5°C. Podaj średnią z drugiego i czwartego dnia w °F."`),
  wiec KAZDE wywolanie narzedzia to porazka (tag `unexpected_tool_call`). Nie ma checku lancucha,
  bo lancuch ma byc pusty.
- **L1** — jedno wywolanie: `get_forecast`. Kolejnosc scisla.
- **L2** — dwa wywolania: `get_weather`, potem `get_forecast`. Kolejnosc scisla.
- **L3N** — cztery wywolania, bez grafu sasiedztwa. Prompt NAKAZUJE dwie **osobne** konwersje
  (`"Przelicz temperaturę drugiego dnia ... narzędziem convert_temperature, a potem tym samym narzędziem
  przelicz temperaturę czwartego dnia"`), wiec jedna konwersja sredniej jest odstepstwem od orkiestracji
  (`wrong_tool_order`), a nie zla arytmetyka. Konwersja jest afiniczna, wiec obie sciezki daja te sama
  liczbe — dlatego "skrot" wykrywa sie po liczbie wywolan `convert_temperature`, nie po wyniku.
- **L3T** — cztery wywolania z pulapka kolejnosci: `find_nearest_city` przed `get_forecast`, prognoza
  dla PIERWSZEGO miasta z otrzymanej listy. Tylko jedna konwersja.

**Golden jest sparowany po literze instancji, nie po szczeblu.** Instancja `_a` ma golden `46.4`
na KAZDYM szczeblu (L0_a = L1_a = L2_a = L3N_a = L3T_a = 46.4); analogicznie `_b`=48.2, `_c`=45.5,
`_d`=47.3, `_e`=46.4, `_f`=45.5, `_g`=35.6, `_h`=41.9, `_i`=42.8, `_j`=43.7. Miedzy szczeblami
zmienia sie WYLACZNIE obciazenie orkiestracyjne. Zrodlo: odczyt `expected_final_state.final_answer_contains_any`
ze wszystkich 46 plikow `tasks/ladder_ext/*.yaml`. `max_steps=8` jest stale dla wszystkich 46 zadan.

### 2. n per szczebel

| szczebel | n |
|---|---|
| L0 | 10 |
| L1 | 10 |
| L2 | 10 |
| L3N | 10 |
| L3T | 6 |
| **razem** | **46** |

Zrodlo: liczba plikow `tasks/ladder_ext/v3_ext_<szczebel>_*.yaml` (`ladder_rungs.txt`, pole `instancji=`)
oraz kontrola z `run.log`: rozklad `{L0:10, L1:10, L2:10, L3N:10, L3T:6}` wystepuje w **14 runach z 14**
(skrypt pomocniczy, blok "n per szczebel").

---

### 3. TABELA A — model x kwant x szczebel, repair OFF

Zrodlo: skrypt pomocniczy `_helpers/ladder_pllum_rungs.py` (tresc w punkcie 8), pliki wejsciowe
`run.log` + `summary.json` z 14 katalogow runow wymienionych na gorze.
Kolumna `kontrola summary` sprawdza, ze suma zdanych per szczebel rowna sie `num_passed` z
`summary.json` — **OK we wszystkich 14 runach**. Osiem wierszy Bielika zgadza sie co do znaku
z TABELA 1 w `analysis_out/ladder_breakdown.txt` (skrypt `analysis/ladder_breakdown.py`).

| model | kwant | L0 (n=10) | L1 (n=10) | L2 (n=10) | L3T (n=6) | L3N (n=10) | RAZEM (n=46) | kontrola summary |
|---|---|---|---|---|---|---|---|---|
| Bielik-11B | Q8_0   | 0/10 0.00 | 1/10 0.10 | 4/10 0.40 | 6/6 1.00 | 2/10 0.20 | 13/46 0.283 | OK |
| Bielik-11B | Q4_K_M | 0/10 0.00 | 0/10 0.00 | 1/10 0.10 | 0/6 0.00 | 0/10 0.00 | 1/46 0.022 | OK |
| Bielik-11B | Q3_K_M | 0/10 0.00 | 10/10 1.00 | 10/10 1.00 | 5/6 0.83 | 7/10 0.70 | 32/46 0.696 | OK |
| Bielik-11B | Q2_K   | 0/10 0.00 | 0/10 0.00 | 0/10 0.00 | 0/6 0.00 | 0/10 0.00 | 0/46 0.000 | OK |
| Bielik-7B | Q8_0   | 0/10 0.00 | 0/10 0.00 | 2/10 0.20 | 0/6 0.00 | 0/10 0.00 | 2/46 0.043 | OK |
| Bielik-7B | Q4_K_M | 0/10 0.00 | 0/10 0.00 | 0/10 0.00 | 0/6 0.00 | 1/10 0.10 | 1/46 0.022 | OK |
| Bielik-7B | Q3_K_M | 0/10 0.00 | 1/10 0.10 | 1/10 0.10 | 0/6 0.00 | 0/10 0.00 | 2/46 0.043 | OK |
| Bielik-7B | Q2_K   | 0/10 0.00 | 0/10 0.00 | 0/10 0.00 | 0/6 0.00 | 0/10 0.00 | 0/46 0.000 | OK |
| PLLuM-8B | Q8_0   | **2/10 0.20** | 0/10 0.00 | 0/10 0.00 | 0/6 0.00 | 0/10 0.00 | 2/46 0.043 | OK |
| PLLuM-8B | Q6_K   | 0/10 0.00 | 0/10 0.00 | 0/10 0.00 | 0/6 0.00 | 0/10 0.00 | 0/46 0.000 | OK |
| PLLuM-8B | Q5_K_M | 0/10 0.00 | 0/10 0.00 | 0/10 0.00 | 0/6 0.00 | 0/10 0.00 | 0/46 0.000 | OK |
| PLLuM-8B | Q4_K_M | 0/10 0.00 | 0/10 0.00 | 0/10 0.00 | 0/6 0.00 | 0/10 0.00 | 0/46 0.000 | OK |
| PLLuM-8B | Q3_K_M | 0/10 0.00 | 0/10 0.00 | 0/10 0.00 | 0/6 0.00 | 0/10 0.00 | 0/46 0.000 | OK |
| PLLuM-8B | Q2_K   | 0/10 0.00 | 0/10 0.00 | 0/10 0.00 | 0/6 0.00 | 0/10 0.00 | 0/46 0.000 | OK |

Fakty odczytane wprost z tabeli:

- L0 = 0.00 w 13 runach z 14. Jedyny wyjatek to **PLLuM Q8_0 = 2/10** (`v3_ext_L0_c` i `v3_ext_L0_f`,
  linie ze znakiem `✓` w `results/v3_pllum_2026-07-29/q8_ladder_no_repair/run.log`).
- PLLuM ma na drabinie **2 zdane zadania na 276** (6 kwantow x 46) i oba sa na L0, czyli na szczeblu
  bez zadnego wywolania narzedzia. Na L1, L2, L3T i L3N PLLuM ma 0 zdanych w kazdym z 6 kwantow.
- Bielik-11B Q3_K_M ma na L1 i L2 komplet 10/10, a Q8_0 odpowiednio 1/10 i 4/10 — kwant nizszy
  bije kwant wyzszy na tych dwoch szczeblach.
- Bielik-11B Q8_0 ma L3T 6/6 = 1.00 przy L3N 2/10 = 0.20, mimo ze oba szczeble maja po 4 wywolania.
- Bielik-11B Q4_K_M: 1/46 = 0.022, czyli o jedno zadanie wiecej niz Q2_K.

**Uwaga o repair ON (poza zakresem tabeli, zrodlo `analysis_out/inventory.txt`, wiersze `ladder46 ON`):**
11B Q8 13/46, Q4 **7/46** (off: 1/46), Q3 32/46, Q2 0/46; 7B Q8 3/46 (off: 2/46), Q4 **9/46** (off: 1/46),
Q3 2/46, Q2 0/46; PLLuM Q8 2/46, pozostale kwanty 0/46. Repair ON zmienia wynik wylacznie w komorkach
Q4 obu Bielikow i w 7B Q8; wszystkie tabele ponizej dotycza wylacznie repair OFF.

---

### 4. TABELA B — L3N: rozbicie porazek (SKROT vs PRAWDZIWY)

Zrodlo: `analysis_out/ladder_breakdown.txt`, TABELA 2 + blok "KONTROLA — pelne wyliczenie L3N"
(skrypt `analysis/ladder_breakdown.py`; wejscie: `run.log` + `trajectories.jsonl` z 8 runow Bielika,
golden z `tasks/ladder_ext/*.yaml`).

Definicja kategorii uzyta w skrypcie:
- **SKROT** — porazka, w ktorej golden JEST obecny w `final_answer`, a `convert_temperature` zostalo
  wywolane dokladnie **raz** zamiast dwa razy (model przeliczyl srednia zamiast dwoch dni osobno).
- **PRAWDZIWY** — wszystko pozostale (golden nieobecny ALBO liczba konwersji rozna od 1).
- rata **scisla** = PASS/10; rata **tolerancyjna na SKROT** = (PASS+SKROT)/10.

| model | kwant | PASS | SKROT | PRAWDZ | rata scisla | rata tolerancyjna na SKROT |
|---|---|---|---|---|---|---|
| Bielik-11B | Q8_0   | 2 | **0** | 8 | 2/10 = 0.20 | 2/10 = 0.20 |
| Bielik-11B | Q4_K_M | 0 | **0** | 10 | 0/10 = 0.00 | 0/10 = 0.00 |
| Bielik-11B | Q3_K_M | 7 | **0** | 3 | 7/10 = 0.70 | 7/10 = 0.70 |
| Bielik-11B | Q2_K   | 0 | **0** | 10 | 0/10 = 0.00 | 0/10 = 0.00 |
| Bielik-7B | Q8_0   | 0 | **0** | 10 | 0/10 = 0.00 | 0/10 = 0.00 |
| Bielik-7B | Q4_K_M | 1 | **0** | 9 | 1/10 = 0.10 | 1/10 = 0.10 |
| Bielik-7B | Q3_K_M | 0 | **0** | 10 | 0/10 = 0.00 | 0/10 = 0.00 |
| Bielik-7B | Q2_K   | 0 | **0** | 10 | 0/10 = 0.00 | 0/10 = 0.00 |

**Kategoria SKROT jest pusta: 0 przypadkow na 80 zadan L3N** (8 runow Bielika x 10 zadan).
Dlatego kolumna "tolerancyjna na SKROT" jest identyczna ze "scisla" w kazdym z 8 wierszy.
Rozszerzenie na PLLuM (skrypt pomocniczy, blok 3): rowniez **0 SKROT na 60 zadan L3N** (6 kwantow x 10),
czyli lacznie **0 na 140** we wszystkich 14 runach drabiny.

Pelne wyliczenie porazek PRAWDZIWYCH — Bielik (`ladder_breakdown.txt`, blok KONTROLA; suma kazdego
wiersza + PASS = 10):

| model | kwant | rozklad (liczba konwersji, golden obecny) -> ile zadan |
|---|---|---|
| Bielik-11B | Q8_0   | konw=2/golden=nie -> 1; konw=2/golden=TAK -> 7 |
| Bielik-11B | Q4_K_M | konw=2/golden=nie -> 6; konw=2/golden=TAK -> 4 |
| Bielik-11B | Q3_K_M | konw=6/golden=nie -> 3 |
| Bielik-11B | Q2_K   | konw=0/golden=nie -> 10 |
| Bielik-7B | Q8_0   | konw=2/golden=nie -> 2; konw=2/golden=TAK -> 7; konw=3/golden=nie -> 1 |
| Bielik-7B | Q4_K_M | konw=0/golden=nie -> 2; konw=2/golden=nie -> 2; konw=2/golden=TAK -> 2; konw=6/golden=nie -> 3 |
| Bielik-7B | Q3_K_M | konw=2/golden=nie -> 4; konw=6/golden=nie -> 6 |
| Bielik-7B | Q2_K   | konw=0/golden=nie -> 10 |

To samo dla PLLuM (skrypt pomocniczy, blok 3; wejscie: `run.log` + `trajectories.jsonl` z 6 runow
`results/v3_pllum_2026-07-29/q*_ladder_no_repair`):

| model | kwant | PASS | SKROT | PRAWDZ | rozklad (konwersji, golden) -> ile |
|---|---|---|---|---|---|
| PLLuM-8B | Q8_0   | 0 | 0 | 10 | konw=0/nie -> 10 |
| PLLuM-8B | Q6_K   | 0 | 0 | 10 | konw=0/nie -> 8; konw=1/nie -> 1; konw=2/nie -> 1 |
| PLLuM-8B | Q5_K_M | 0 | 0 | 10 | konw=0/nie -> 10 |
| PLLuM-8B | Q4_K_M | 0 | 0 | 10 | konw=0/nie -> 1; konw=1/nie -> 7; konw=2/nie -> 2 |
| PLLuM-8B | Q3_K_M | 0 | 0 | 10 | konw=0/nie -> 4; konw=1/nie -> 1; konw=2/nie -> 4; konw=3/nie -> 1 |
| PLLuM-8B | Q2_K   | 0 | 0 | 10 | konw=0/nie -> 7; konw=2/nie -> 3 |

W zadnej z 60 porazek L3N PLLuM golden NIE jest obecny w `final_answer` (kolumna golden = "nie"
w kazdym wierszu). Konsekwencja: dla PLLuM zadna rata tolerancyjna (ani na SKROT, ani na typowanie
z punktu 5) nie moze podniesc L3N powyzej 0.00.

---

### 5. TABELA C — rata tolerancyjna wg typowania pola `answer`

Zrodlo: `analysis_out/ladder_typing_tolerant.txt`, TABELA 3 (skrypt `analysis/ladder_typing_tolerant.py`;
wejscie takie jak w `ladder_breakdown.py`). Obejmuje **wylacznie 8 runow Bielika**.

Kryterium darowania (dokladnie z kodu): darowana jest porazka, w ktorej **jednoczesnie**
(a) zbior tagow oracle jest niepusty i zawiera sie w `FMT_ONLY = {final_answer_missing,
schema_violation, invalid_json, final_answer_shape_violation}` — czyli oracle nie zglosil zadnego
zarzutu do lancucha ani do tresci, oraz (b) wartosc `final_answer` zawiera golden, ale **nie jest
stringiem** (`not isinstance(val, str)`).

Format komorki: `scisle_PASS + darowane_na_typowaniu = razem/n (rata)`.

| model | kwant | L0 | L1 | L2 | L3T | L3N | RAZEM |
|---|---|---|---|---|---|---|---|
| Bielik-11B | Q8_0   | 0+0=0/10 (0.00) | 1+0=1/10 (0.10) | 4+0=4/10 (0.40) | 6+0=6/6 (1.00) | **2+7=9/10 (0.90)** | 13+7=20/46 (0.435) |
| Bielik-11B | Q4_K_M | 0+0=0/10 (0.00) | 0+0=0/10 (0.00) | 1+0=1/10 (0.10) | 0+0=0/6 (0.00) | 0+4=4/10 (0.40) | 1+4=5/46 (0.109) |
| Bielik-11B | Q3_K_M | 0+0=0/10 (0.00) | 10+0=10/10 (1.00) | 10+0=10/10 (1.00) | 5+0=5/6 (0.83) | 7+0=7/10 (0.70) | 32+0=32/46 (0.696) |
| Bielik-11B | Q2_K   | 0+0=0/10 (0.00) | 0+0=0/10 (0.00) | 0+0=0/10 (0.00) | 0+0=0/6 (0.00) | 0+0=0/10 (0.00) | 0+0=0/46 (0.000) |
| Bielik-7B | Q8_0   | 0+0=0/10 (0.00) | 0+0=0/10 (0.00) | 2+0=2/10 (0.20) | 0+0=0/6 (0.00) | **0+7=7/10 (0.70)** | 2+7=9/46 (0.196) |
| Bielik-7B | Q4_K_M | 0+0=0/10 (0.00) | 0+0=0/10 (0.00) | 0+0=0/10 (0.00) | 0+0=0/6 (0.00) | 1+2=3/10 (0.30) | 1+2=3/46 (0.065) |
| Bielik-7B | Q3_K_M | 0+0=0/10 (0.00) | 1+0=1/10 (0.10) | 1+0=1/10 (0.10) | 0+0=0/6 (0.00) | 0+0=0/10 (0.00) | 2+0=2/46 (0.043) |
| Bielik-7B | Q2_K   | 0+0=0/10 (0.00) | 0+0=0/10 (0.00) | 0+0=0/10 (0.00) | 0+0=0/6 (0.00) | 0+0=0/10 (0.00) | 0+0=0/46 (0.000) |

**Potwierdzenie liczb z zadania** — `ladder_typing_tolerant.txt`, blok "Podsumowanie L3N — trzy raty
obok siebie", przepisany co do znaku:

| model | kwant | L3N scisla | L3N tolerancyjna SKROT | L3N tolerancyjna TYPOWANIE |
|---|---|---|---|---|
| Bielik-11B | Q8_0   | 2/10 = 0.20 | 2/10 = 0.20 | **9/10 = 0.90** |
| Bielik-11B | Q4_K_M | 0/10 = 0.00 | 0/10 = 0.00 | 4/10 = 0.40 |
| Bielik-11B | Q3_K_M | 7/10 = 0.70 | 7/10 = 0.70 | 7/10 = 0.70 |
| Bielik-11B | Q2_K   | 0/10 = 0.00 | 0/10 = 0.00 | 0/10 = 0.00 |
| Bielik-7B | Q8_0   | 0/10 = 0.00 | 0/10 = 0.00 | **7/10 = 0.70** |
| Bielik-7B | Q4_K_M | 1/10 = 0.10 | 1/10 = 0.10 | 3/10 = 0.30 |
| Bielik-7B | Q3_K_M | 0/10 = 0.00 | 0/10 = 0.00 | 0/10 = 0.00 |
| Bielik-7B | Q2_K   | 0/10 = 0.00 | 0/10 = 0.00 | 0/10 = 0.00 |

Obie liczby z zadania **POTWIERDZONE w pliku**: 11B Q8_0 L3N `0.20 -> 0.90` (2 scisle + 7 darowanych),
7B Q8_0 L3N `0.00 -> 0.70` (0 scislych + 7 darowanych). Darowanie dziala WYLACZNIE na L3N — kolumny
L0, L1, L2 i L3T maja `+0` w kazdym z 8 wierszy.

**Ksztalt darowanych odpowiedzi** (zrodlo: `analysis_out/ladder_nearmiss.txt`, skrypt `analysis/ladder_nearmiss.py`):

- Bielik-11B Q8_0, 8 porazek L3N z dwiema konwersjami: `final_answer` istnieje TYLKO w surowym
  wyjsciu modelu (`TYLKO SUROWY(float)`), wartosci `'48.2'`, `'45.5'`, `'46.4'`, `'45.5'`, `'35.6'`,
  `'42.4'`, `'42.8'`, `'43.7'` — golden trafiony w 7 z 8 (nietrafiony: `v3_ext_L3N_h`, model 42.4
  przy goldenie 41.9). Tagi we wszystkich osmiu: `['final_answer_missing', 'schema_violation']`.
- Bielik-7B Q8_0, 9 porazek L3N z dwiema konwersjami: `TYLKO SUROWY(dict)`, np.
  `{'average_fahrenheit': 46.4}`, `{'average_temperature_fahrenheit': 48.2}`,
  `{'average_temperature_f': 43.7}` — golden trafiony w 7 z 9. Tagi:
  `['final_answer_missing', 'invalid_json', 'schema_violation']`.
- Bielik-11B Q4_K_M, 10 porazek: `TYLKO SUROWY(float)`, golden trafiony w 4 z 10; wsrod nietrafionych
  cztery razy wartosc `'13.5'`.
- Bielik-7B Q4_K_M, 4 porazki z dwiema konwersjami: golden trafiony w 2 (`'46.4'`, `'42.8'`);
  jedna z nich (`v3_ext_L3N_g`) ma tagi tresciowe (`unknown_action`, `wrong_tool_order`), wiec nie
  kwalifikuje sie do darowania.

---

### 6. Kontrole

Zrodlo: `analysis_out/ladder_controls.txt` (skrypt `analysis/ladder_controls.py`; wejscie jak w
`ladder_breakdown.py`), uzupelnione blokiem 2 skryptu pomocniczego.

#### 6a. Dlaczego L1 i L2 NIE sa darowane

Zarzut brzmialby: "L1 i L2 na 11B Q8 maja te same tagi formatu co darowane L3N, wiec darowanie jest
arbitralne". Wyliczenie po zadaniu (11B Q8_0, `results/v3_11b_ladder_2026-07-29/q8_no_repair`):

L1 — 1 PASS (`v3_ext_L1_f`), 9 FAIL, kazda z tagami `['final_answer_missing', 'schema_violation']`,
i w kazdej **golden jest NIEOBECNY**:

| zadanie | golden | odpowiedz modelu |
|---|---|---|
| `v3_ext_L1_a` | 46.4 | 59 |
| `v3_ext_L1_b` | 48.2 | 54.2 |
| `v3_ext_L1_c` | 45.5 | 51 |
| `v3_ext_L1_d` | 47.3 | 54.8 |
| `v3_ext_L1_e` | 46.4 | 59 |
| `v3_ext_L1_g` | 35.6 | 34.7 |
| `v3_ext_L1_h` | 41.9 | 59 |
| `v3_ext_L1_i` | 42.8 | 59 |
| `v3_ext_L1_j` | 43.7 | 59 |

L2 — 4 PASS (`_a`, `_c`, `_d`, `_h`), 6 FAIL, te same tagi, golden NIEOBECNY w kazdej:

| zadanie | golden | odpowiedz modelu |
|---|---|---|
| `v3_ext_L2_b` | 48.2 | 56.3 |
| `v3_ext_L2_e` | 46.4 | 52 |
| `v3_ext_L2_f` | 45.5 | 54.6 |
| `v3_ext_L2_g` | 35.6 | 50 |
| `v3_ext_L2_i` | 42.8 | 59 |
| `v3_ext_L2_j` | 43.7 | 51.2 |

Czyli: warunek (a) darowania (same tagi formatu) jest na L1 i L2 spelniony, ale warunek (b)
(golden obecny w wartosci `answer`) **nie** — model podaje inna liczbe. Darowanie na L3N nie jest
wiec darmowym punktem rozdanym wszystkim porazkom z tagami formatu: na 15 porazkach L1+L2 tego typu
darowanie dalo **0** dodatkowych zaliczen (kolumny L1 i L2 w TABELA C maja `+0`).

#### 6b. L0 = 0.00 — dwie rozne przyczyny

`ladder_controls.txt` pokazuje 4 runy (11B Q8, 11B Q3, 7B Q8, 11B Q2); ponizej komplet 14 (skrypt
pomocniczy, blok 2; wywolania narzedzi liczone z `trajectories.jsonl` jako
`parsed_action.action == "call_tool"`).

| model | kwant | L0 PASS | wywolan narzedzi razem | zadan z >=1 wywolaniem | tagi L0 |
|---|---|---|---|---|---|
| Bielik-11B | Q8_0   | 0/10 | 18 | 10/10 | `unexpected_tool_call`:10, `wrong_final_answer`:5, `no_json_found`:1 |
| Bielik-11B | Q4_K_M | 0/10 | 20 | 10/10 | `unexpected_tool_call`:10, `wrong_final_answer`:5, `invalid_json`:1, `schema_violation`:1, `final_answer_missing`:1 |
| Bielik-11B | Q3_K_M | 0/10 | 18 | 10/10 | `unexpected_tool_call`:10, `wrong_final_answer`:5, `no_json_found`:4 |
| Bielik-11B | Q2_K   | 0/10 | **0** | 0/10 | `wrong_final_answer`:10 |
| Bielik-7B | Q8_0   | 0/10 | **0** | 0/10 | `unknown_action`:10, `final_answer_missing`:9, `schema_violation`:3, `wrong_final_answer`:1, `invalid_json`:1 |
| Bielik-7B | Q4_K_M | 0/10 | 15 | 4/10 | `unknown_action`:10, `final_answer_missing`:7, `unexpected_tool_call`:4 |
| Bielik-7B | Q3_K_M | 0/10 | 50 | 8/10 | `final_answer_missing`:8, `unexpected_tool_call`:8, `schema_violation`:5, `wrong_final_answer`:2 |
| Bielik-7B | Q2_K   | 0/10 | 80 | 10/10 | `final_answer_missing`:10, `unexpected_tool_call`:10 |
| PLLuM-8B | Q8_0   | **2/10** | **0** | 0/10 | `wrong_final_answer`:8 |
| PLLuM-8B | Q6_K   | 0/10 | **0** | 0/10 | `wrong_final_answer`:10 |
| PLLuM-8B | Q5_K_M | 0/10 | **0** | 0/10 | `wrong_final_answer`:10 |
| PLLuM-8B | Q4_K_M | 0/10 | **0** | 0/10 | `wrong_final_answer`:10 |
| PLLuM-8B | Q3_K_M | 0/10 | **0** | 0/10 | `wrong_final_answer`:10 |
| PLLuM-8B | Q2_K   | 0/10 | 11 | 10/10 | `unexpected_tool_call`:10, `wrong_final_answer`:6 |

**Przyczyna 1 — zlamanie zakazu.** Bielik-11B Q8/Q4/Q3 wola narzedzia w 10 zadaniach na 10 mimo
`no_tool_calls: true` (18-20 wywolan na run, czyli 1-2 na zadanie; `ladder_controls.txt` podaje dla
11B Q8 i 11B Q3 wektor wywolan `[1, 2, 2, 2, 1, 2, 2, 2, 2, 2]`). Tag `unexpected_tool_call` = 10/10.
Ten sam mechanizm dotyczy Bielik-7B Q2_K (80 wywolan, 10/10 zadan) i PLLuM Q2_K (11 wywolan, 10/10
zadan; w `run.log` widac np. `convert_temperature(value=7.5, from_unit='celsius', to_unit='fahrenheit') -> final_answer`).

**Przyczyna 2 — posluszenstwo, ale zla odpowiedz lub zepsuta koperta.** Bielik-11B Q2_K, Bielik-7B Q8_0
i PLLuM Q8/Q6/Q5/Q4/Q3 nie wolaja narzedzia ANI RAZU (0 wywolan, 0/10 zadan z wywolaniem) — zakaz L0
jest respektowany. Odpadaja z dwoch osobnych powodow:
- **zla liczba**: 11B Q2_K `wrong_final_answer` 10/10; PLLuM Q6/Q5/Q4/Q3 `wrong_final_answer` 10/10;
  PLLuM Q8_0 `wrong_final_answer` 8/10 (dwa zadania zdane — jedyne 2 zaliczenia L0 w calej drabinie).
- **zepsuta koperta**: 7B Q8_0 `unknown_action` 10/10 + `final_answer_missing` 9/10 — model nie
  wystawia poprawnego `final_answer`, wiec zawartosc odpowiedzi nie jest nawet oceniana.

Podsumowanie liczbowe: identyczna wartosc L0 = 0.00 stoi na dwoch rozlacznych mechanizmach —
grupa "wola mimo zakazu" (11B Q8/Q4/Q3, 7B Q4/Q3/Q2, PLLuM Q2 = 7 runow) i grupa "nie wola, ale nie
trafia albo nie umie sformatowac" (11B Q2, 7B Q8, PLLuM Q8/Q6/Q5/Q4/Q3 = 7 runow). Bielik-7B Q4_K_M
i Q3_K_M sa mieszane (4/10 i 8/10 zadan z wywolaniem), ale w obu tag `unexpected_tool_call` wystepuje,
wiec zaliczone sa do grupy pierwszej.

---

### 7. BRAK DANYCH

- **Rata tolerancyjna wg typowania dla PLLuM** nie jest policzona w `analysis_out/ladder_typing_tolerant.txt`
  — skrypt `analysis/ladder_typing_tolerant.py` ma na sztywno liste 8 runow Bielika (stala `RUNS`).
  Z bloku 3 skryptu pomocniczego wynika fakt rozstrzygajacy dla L3N: w zadnej z 60 porazek L3N PLLuM
  golden nie jest obecny w `final_answer`, wiec warunek (b) darowania nie moze byc spelniony i L3N
  PLLuM pozostaje 0.00 przy kazdej z trzech rat. Dla L0/L1/L2/L3T PLLuM rata tolerancyjna NIE zostala
  policzona.
- **Rozbicie SKROT/PRAWDZIWY dla runow z repair ON** nie istnieje w zadnym gotowym wyjsciu; wszystkie
  skrypty drabiny maja w `RUNS` wylacznie warianty `no_repair`. Dostepne sa tylko sumy 46-zadaniowe
  z `inventory.txt`.
- **Kwanty Q5_K_M i Q6_K dla obu Bielikow na drabinie**: w `results/` sa tylko katalogi `q{8,4,3,2}`
  (`v3_11b_ladder_2026-07-29`, `v3_7b_ladder_2026-07-29`). Drabina Bielika ma 4 kwanty, PLLuM 6 —
  tabela model x kwant x szczebel jest z tego powodu nierownomierna i nie da sie jej uzupelnic
  z danych na dysku.
- **Powod, dla ktorego darowane odpowiedzi maja typ float/dict zamiast string**, nie jest ustalany
  przez zadne z wyjsc — `ladder_nearmiss.txt` podaje sam ksztalt (`TYLKO SUROWY(float)` /
  `TYLKO SUROWY(dict)`) i tagi, bez przyczyny.

---

### 8. Skrypt pomocniczy

Zapisany w `<katalog_sekcji>/_helpers/ladder_pllum_rungs.py` — **NIE w repo**. Uruchamiany z katalogu
glownego repo:

```
cd /c/Users/japre/polagentbench && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe \
  "<katalog_sekcji>/_helpers/ladder_pllum_rungs.py"
```

Powstal, bo `analysis/ladder_breakdown.py` obejmuje wylacznie 8 runow Bielika — brakowalo 6 runow PLLuM
w tabeli model x kwant x szczebel, kompletu przyczyn L0 (`analysis/ladder_controls.py` pokazuje 4 runy
z 14) oraz rozbicia L3N dla PLLuM. Metoda przepisana 1:1 z `analysis/ladder_breakdown.py` i
`analysis/ladder_controls.py`; osiem wierszy Bielika w wyjsciu sluzy jako kontrola zgodnosci
z TABELA 1 w `ladder_breakdown.txt` (zgadza sie co do znaku).

```python
# -*- coding: utf-8 -*-
"""
Drabina L0-L3N: pass rate per szczebel dla WSZYSTKICH TRZECH modeli, w tym PLLuM.

Powod istnienia: analysis/ladder_breakdown.py obejmuje tylko 2 modele Bielik (8 runow).
Ten skrypt dokłada 6 runow PLLuM (q{2,3,4,5,6,8}_ladder_no_repair) tą samą metodą:
werdykt czytany z run.log (oracle), nigdy z trajectory.success.

Kolumny Bielika sluza jako KONTROLA - musza zgadzac sie co do znaku z TABELA 1
w analysis_out/ladder_breakdown.txt, a RAZEM z num_passed w summary.json.

CZYTA Z:
  results/v3_11b_ladder_2026-07-29/q{8,4,3,2}_no_repair/run.log
  results/v3_7b_ladder_2026-07-29/q{8,4,3,2}_no_repair/run.log
  results/v3_pllum_2026-07-29/q{8,6,5,4,3,2}_ladder_no_repair/{run.log,summary.json}

TYLKO ODCZYT. Uruchamiac z katalogu glownego repo:
  .venv/Scripts/python.exe <sciezka>/ladder_pllum_rungs.py
"""
import json, re, sys, os, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RUNS = [("Bielik-11B", q, f"results/v3_11b_ladder_2026-07-29/{p}_no_repair")
        for q, p in [("Q8_0","q8"),("Q4_K_M","q4"),("Q3_K_M","q3"),("Q2_K","q2")]]
RUNS += [("Bielik-7B", q, f"results/v3_7b_ladder_2026-07-29/{p}_no_repair")
         for q, p in [("Q8_0","q8"),("Q4_K_M","q4"),("Q3_K_M","q3"),("Q2_K","q2")]]
RUNS += [("PLLuM-8B", q, f"results/v3_pllum_2026-07-29/{p}_ladder_no_repair")
         for q, p in [("Q8_0","q8"),("Q6_K","q6"),("Q5_K_M","q5"),
                      ("Q4_K_M","q4"),("Q3_K_M","q3"),("Q2_K","q2")]]

RUNGS = ["L0", "L1", "L2", "L3T", "L3N"]

def rung(tid):
    m = re.match(r"v3_ext_(L3N|L3T|L0|L1|L2)_", tid)
    return m.group(1) if m else None

def verdicts(run):
    """Werdykt = znak z run.log. Ten sam parser co analysis/ladder_breakdown.py."""
    v = {}
    for ln in open(f"{run}/run.log", encoding="utf-8"):
        m = re.match(r"^(\S+)\s+([✓✗?])\s+(.*)$", ln.rstrip("\n"))
        if m:
            tail = m.group(3); tg = set()
            if " - " in tail:
                tg = {t.strip() for t in tail.rsplit(" - ", 1)[1].split(",")}
            v[m.group(1)] = ("PASS" if m.group(2) == "✓" else "FAIL", tg)
    return v

print("TABELA — pass rate per szczebel, wszystkie 3 modele (repair OFF, T=0, seed=42)")
hdr = f"{'model':<12}{'kwant':<9}"
print(hdr + "".join(f"{r:>14}" for r in RUNGS) + f"{'RAZEM':>15}{'summary':>10}")
print("-" * (21 + 14 * 5 + 25))
prev = None
for model, quant, run in RUNS:
    if prev is not None and model != prev:
        print()
    prev = model
    v = verdicts(run)
    per = {r: [0, 0] for r in RUNGS}
    for tid, (st, tg) in v.items():
        r = rung(tid)
        if r is None:
            continue
        per[r][1] += 1
        if st == "PASS":
            per[r][0] += 1
    tp = sum(p for p, _ in per.values()); tt = sum(t for _, t in per.values())
    s = json.load(open(f"{run}/summary.json", encoding="utf-8"))
    cells = "".join(f"{f'{p}/{t}  {p/t:.2f}':>14}" for p, t in (per[r] for r in RUNGS))
    ok = "OK" if s["num_passed"] == tp else f"ROZJAZD({s['num_passed']})"
    print(f"{model:<12}{quant:<9}{cells}{f'{tp}/{tt}  {tp/tt:.3f}':>15}{ok:>10}")

print()
print("n per szczebel (z liczby zadan w run.log, run po runie — musi byc stale):")
sizes = collections.Counter()
for model, quant, run in RUNS:
    per = collections.Counter(rung(t) for t in verdicts(run) if rung(t))
    sizes[tuple(sorted(per.items()))] += 1
for k, n in sizes.items():
    print(f"  {dict(k)}  -> wystepuje w {n} runach z {len(RUNS)}")

# ---- Blok 2: przyczyna L0 we WSZYSTKICH 14 runach --------------------------
# analysis/ladder_controls.py pokazuje tylko 4 runy; tu domykamy komplet.
# Wywolania narzedzi liczone z trajectories.jsonl (parsed_action.action == call_tool),
# tak samo jak w ladder_controls.py.
print()
print("=== L0: przyczyna, wszystkie 14 runow (L0 ZABRANIA wywolan narzedzi) ===")
print(f"{'model':<12}{'kwant':<9}{'PASS':>5}{'wyw.narz.':>11}{'zadan z >=1 wyw.':>18}   tagi")
print("-" * 100)
prev = None
for model, quant, run in RUNS:
    if prev is not None and model != prev:
        print()
    prev = model
    v = verdicts(run)
    trajs = {t["task_id"]: t for t in
             (json.loads(l) for l in open(f"{run}/trajectories.jsonl", encoding="utf-8"))}
    tags = collections.Counter(); ncalls = []; npass = 0
    for tid, (st, tg) in v.items():
        if not tid.startswith("v3_ext_L0_"):
            continue
        if st == "PASS":
            npass += 1
        tags.update(tg)
        ncalls.append(sum(1 for s in trajs[tid]["steps"]
                          if (s["parsed_action"] or {}).get("action") == "call_tool"))
    withcall = sum(1 for c in ncalls if c > 0)
    print(f"{model:<12}{quant:<9}{f'{npass}/10':>5}{sum(ncalls):>11}{f'{withcall}/10':>18}   "
          f"{dict(sorted(tags.items(), key=lambda kv: -kv[1]))}")

# ---- Blok 3: L3N PLLuM — rozbicie porazek ta sama metoda co ladder_breakdown.py ----
import glob, yaml
GOLD = {}
for f in glob.glob("tasks/ladder_ext/v3_ext_*.yaml"):
    d = yaml.safe_load(open(f, encoding="utf-8"))
    GOLD[d["id"]] = [str(x) for x in d["expected_final_state"].get("final_answer_contains_any", [])]

def json_objects(text):
    out, depth, start, instr, esc = [], 0, None, False, False
    for i, ch in enumerate(text):
        if instr:
            if esc: esc = False
            elif ch == chr(92): esc = True
            elif ch == '"': instr = False
            continue
        if ch == '"': instr = True; continue
        if ch == "{":
            if depth == 0: start = i
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    try: out.append(json.loads(text[start:i + 1]))
                    except Exception: pass
                    start = None
    return out

def answer_text(t):
    for s in reversed(t["steps"]):
        pa = s["parsed_action"] or {}
        if pa.get("action") == "final_answer":
            return str(pa.get("answer", ""))
    for s in reversed(t["steps"]):
        for o in json_objects(s["raw_model_output"]):
            if isinstance(o, dict) and o.get("action") == "final_answer" and "answer" in o:
                return str(o["answer"])
    return ""

print()
print("=== L3N PLLuM: rozbicie porazek (SKROT = golden obecny przy 1 konwersji zamiast 2) ===")
print(f"{'kwant':<9}{'PASS':>6}{'SKROT':>7}{'PRAWDZ':>8}   rozklad (konwersji, golden) -> ile")
print("-" * 100)
for model, quant, run in RUNS:
    if model != "PLLuM-8B":
        continue
    v = verdicts(run)
    trajs = {t["task_id"]: t for t in
             (json.loads(l) for l in open(f"{run}/trajectories.jsonl", encoding="utf-8"))}
    npass = skrot = 0; agg = collections.Counter()
    for tid, (st, tg) in v.items():
        if not tid.startswith("v3_ext_L3N_"):
            continue
        if st == "PASS":
            npass += 1; continue
        t = trajs[tid]
        ans = answer_text(t)
        hit = any(g in ans for g in GOLD[tid])
        c = sum(1 for s in t["steps"]
                if (s["parsed_action"] or {}).get("action") == "call_tool"
                and (s["parsed_action"] or {}).get("tool") == "convert_temperature")
        if hit and c == 1:
            skrot += 1
        else:
            agg[(c, "TAK" if hit else "nie")] += 1
    prawdz = sum(agg.values())
    rozk = "  ".join(f"konw={c}/golden={h}->{n}" for (c, h), n in sorted(agg.items()))
    print(f"{quant:<9}{npass:>6}{skrot:>7}{prawdz:>8}   {rozk}")
```

---


<!-- source section: 03_sensitivity.md -->

## Sensitivity analysis typowania (strict vs corrected)

Wszystkie liczby ponizej pochodza albo z gotowych wyjsc `analysis/*.py` zapisanych w
`scratchpad\analysis_out\<nazwa>.txt`, albo z wlasnych skryptow TYLKO-DO-ODCZYTU zapisanych w
`scratchpad\sections\_helpers\typing_*.py` (kazdy taki przypadek jest oznaczony przy tabeli).
Zadnego runu modelu nie powtarzano, zadnego GPU nie uzyto.

Werdykt PASS/FAIL i zestaw tagow bierze sie **wylacznie z `run.log`** kazdego runu (parser
`verdicts()`, identyczny w `ladder_breakdown.py`, `ladder_typing_tolerant.py`, `ladder_controls.py`,
`ladder_nearmiss.py`). Nigdzie nie uzyto `trajectory.success` i nigdzie nie odtwarzano oracle
kodem HEAD — kod ewaluatora sluzy w tej sekcji tylko do zacytowania definicji schematu.

---

### 0. Zakres i proweniencja runow

Suita: **ladder46** = `tasks/ladder_ext/*.yaml` = 46 zadan. Rozklad na szczeble
(`analysis/ladder_rungs.py` -> `analysis_out/ladder_rungs.txt`):
L0 = 10, L1 = 10, L2 = 10, L3T = 6, L3N = 10; razem 46.

Wszystkie osiem komorek analizy typowania to **repair off**:

| model | kwant | katalog runu | commit | run.log | n | seed | temperature | num_passed |
|---|---|---|---|---|---|---|---|---|
| Bielik-11B | Q8_0 | `results/v3_11b_ladder_2026-07-29/q8_no_repair` | e584b38 | TAK | 46 | 42 | 0.0 | 13 |
| Bielik-11B | Q4_K_M | `results/v3_11b_ladder_2026-07-29/q4_no_repair` | e584b38 | TAK | 46 | 42 | 0.0 | 1 |
| Bielik-11B | Q3_K_M | `results/v3_11b_ladder_2026-07-29/q3_no_repair` | e584b38 | TAK | 46 | 42 | 0.0 | 32 |
| Bielik-11B | Q2_K | `results/v3_11b_ladder_2026-07-29/q2_no_repair` | e584b38 | TAK | 46 | 42 | 0.0 | 0 |
| Bielik-7B | Q8_0 | `results/v3_7b_ladder_2026-07-29/q8_no_repair` | e584b38 | TAK | 46 | 42 | 0.0 | 2 |
| Bielik-7B | Q4_K_M | `results/v3_7b_ladder_2026-07-29/q4_no_repair` | e584b38 | TAK | 46 | 42 | 0.0 | 1 |
| Bielik-7B | Q3_K_M | `results/v3_7b_ladder_2026-07-29/q3_no_repair` | e584b38 | TAK | 46 | 42 | 0.0 | 2 |
| Bielik-7B | Q2_K | `results/v3_7b_ladder_2026-07-29/q2_no_repair` | e584b38 | TAK | 46 | 42 | 0.0 | 0 |

Zrodla kolumn: `commit` i `run.log` — `analysis/inventory.py` -> `analysis_out/inventory.txt`
(wiersze 3-10 i 51-58). `seed`, `temperature`, `num_passed`, `num_inconclusive=0` — odczyt
`{summary.json, trajectories.jsonl}` kazdego z 14 katalogow drabiny; `seed` i `temperature` nie sa
zapisane w `summary.json` (oba `None`), wiec wziete z rekordow `trajectories.jsonl`, gdzie kazdy z
46 rekordow ma `seed=42` i `temperature=0.0` w kazdym z 14 katalogow.

Naglowek `TABELA 1` w `ladder_breakdown.txt` deklaruje "repair OFF, T=0, seed=42" jako staly tekst
w kodzie — powyzsza tabela jest niezaleznym potwierdzeniem tej deklaracji z danych.

---

### 1. Na czym dokladnie polega korekta typowania

#### 1.1 Co odrzuca schemat (kod ewaluatora)

`src/polagentbench/protocol.py:63-74`:

```python
class FinalAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["final_answer"]
    answer: str = Field(min_length=1, description="Final natural-language reply.")
```

Pole `answer` jest typu `str`. Kazde `{"action":"final_answer","answer":<nie-string>}` wywraca sie w
`_ACTION_ADAPTER.validate_python` i dostaje kategorie `schema_violation`
(`protocol.py:227-234`). Skoro krok nie sparsowal sie na `FinalAnswer`, trajektoria nie ma zadnego
finalnego dzialania i oracle dokleja `final_answer_missing` (`eval/smoke.py:310`, `:466`).

#### 1.2 Regula korekty (kod, dokladnie)

`analysis/ladder_typing_tolerant.py:27` i `:93-96`:

```python
FMT_ONLY={"final_answer_missing","schema_violation","invalid_json","final_answer_shape_violation"}
...
if tg and tg<=FMT_ONLY:
    val=answer_val(trajs[tid])
    if val is not None and not isinstance(val,str) and any(g in str(val) for g in GOLD[tid]):
        per[r][1]+=1
```

Zadanie zmienia werdykt z FAIL na "darowane" wtedy i tylko wtedy, gdy zachodza **wszystkie trzy**
warunki:

1. **Tagi wylacznie formatowe.** Zbior tagow z `run.log` jest niepusty i jest podzbiorem
   `FMT_ONLY`. Praktyczna konsekwencja: `tools_called_in_order_strict` musial przejsc, bo inaczej w
   zbiorze bylby tag trescowy (`wrong_tool_order`, `unexpected_tool_call`, `unknown_action`,
   `wrong_final_answer`, `no_json_found`).
2. **Wartosc `answer` da sie odzyskac.** `answer_val()` (`:57-64`) najpierw szuka od konca kroku ze
   sparsowanym `parsed_action.action == "final_answer"` i bierze `answer`; jesli takiego nie ma,
   skanuje `raw_model_output` skanerem nawiasow i bierze pierwszy od konca obiekt JSON z
   `action=="final_answer"` i kluczem `"answer"`.
3. **Typ nie-string + golden jako podciag.** `not isinstance(val, str)` **oraz**
   `any(g in str(val) for g in GOLD[tid])`, gdzie `GOLD[tid]` to lista `final_answer_contains_any`
   z YAML-a zadania (dla drabiny zawsze dwa warianty, np. `['46.4', '46,4']`).

Dwie wlasnosci reguly, wprost z kodu: test golden jest testem **podciagu** na `str(val)`, nie
rownosci; a `str(val)` dla dict-a to Pythonowy `repr` (`{'average_fahrenheit': 46.4}`), wiec liczba
wewnatrz slownika liczy sie jako trafienie.

#### 1.3 Jaki typ jest akceptowany dodatkowo — potwierdzenie README kodem i wyjsciem

`analysis/README.md:64` mowi: "odrzucone na **typie** pola `answer` (float w 11B, dict w 7B)".
To samo w naglowku `analysis/ladder_nearmiss.py:8`.

Potwierdzenie w kodzie: regula nie wymienia zadnego konkretnego typu — akceptuje **kazdy typ inny
niz `str`** (`not isinstance(val,str)`). "float / dict" to opis tego, co faktycznie wystapilo w
danych, a nie warunek w kodzie.

Potwierdzenie w wyjsciu — typy 20 faktycznie darowanych rekordow
(`_helpers/typing_forgiven_list.py`, linia `ZBIORCZO`):

| model | typ pola `answer` w darowanych | liczba |
|---|---|---|
| Bielik-11B | `float` | 11 |
| Bielik-7B | `dict` | 7 |
| Bielik-7B | `float` | 2 |

**Sprostowanie do README:** "dict w 7B" jest prawdziwe dla **7B Q8_0** (7 z 7 darowanych to dict),
ale nieprawdziwe dla **7B Q4_K_M**, gdzie oba darowane rekordy (`v3_ext_L3N_e`, `v3_ext_L3N_i`) maja
typ `float` — widac to takze wprost w `analysis_out/ladder_nearmiss.txt`, sekcja "Bielik-7B Q4_K_M",
gdzie kazdy wiersz ma `TYLKO SUROWY(float)`. Dla 11B "float" zgadza sie w 100% (11 z 11).

Trzecia obserwacja z kodu i danych: **zaden** z 20 darowanych rekordow nie pochodzil ze
sparsowanego `final_answer` — wszystkie 20 maja zrodlo `SUROWY`, co jest wymuszone przez schemat
(nie-string nigdy nie sparsuje sie na `FinalAnswer`). Tag `final_answer_shape_violation`, mimo ze
jest w `FMT_ONLY`, **nie wystepuje ani razu** w zadnym z osmiu `run.log` (`grep -c` = 0 w kazdym) —
zadania drabiny deklaruja tylko checki `final_answer_contains_any`, `final_answer_used`,
`tools_called_in_order_strict` (`analysis_out/ladder_rungs.txt`), a tag ten produkuje check
`_check_final_answer_is_string` (`eval/smoke.py:635-683`), ktorego tu nie ma.

---

### 2. Pelna tabela: model x kwant x szczebel, rata scisla vs skorygowana

Zrodla: rata **scisla** — `analysis/ladder_breakdown.py` -> `analysis_out/ladder_breakdown.txt`,
TABELA 1. Rata **skorygowana** — `analysis/ladder_typing_tolerant.py` ->
`analysis_out/ladder_typing_tolerant.txt`, TABELA 3 (komorka `scisle_PASS + darowane = razem/n`).
Wejscie obu: `results/v3_11b_ladder_2026-07-29/*_no_repair/{run.log,trajectories.jsonl}`,
`results/v3_7b_ladder_2026-07-29/*_no_repair/{run.log,trajectories.jsonl}`, `tasks/ladder_ext/*.yaml`.
Kolumny `delta` to roznica dwoch liczb z tych dwoch plikow.

#### 2.1 Zaliczenia (liczby zadan): scisla -> skorygowana (delta)

| model | kwant | L0 (n=10) | L1 (n=10) | L2 (n=10) | L3T (n=6) | L3N (n=10) | RAZEM (n=46) |
|---|---|---|---|---|---|---|---|
| Bielik-11B | Q8_0 | 0 -> 0 (0) | 1 -> 1 (0) | 4 -> 4 (0) | 6 -> 6 (0) | **2 -> 9 (+7)** | **13 -> 20 (+7)** |
| Bielik-11B | Q4_K_M | 0 -> 0 (0) | 0 -> 0 (0) | 1 -> 1 (0) | 0 -> 0 (0) | **0 -> 4 (+4)** | **1 -> 5 (+4)** |
| Bielik-11B | Q3_K_M | 0 -> 0 (0) | 10 -> 10 (0) | 10 -> 10 (0) | 5 -> 5 (0) | 7 -> 7 (0) | 32 -> 32 (0) |
| Bielik-11B | Q2_K | 0 -> 0 (0) | 0 -> 0 (0) | 0 -> 0 (0) | 0 -> 0 (0) | 0 -> 0 (0) | 0 -> 0 (0) |
| Bielik-7B | Q8_0 | 0 -> 0 (0) | 0 -> 0 (0) | 2 -> 2 (0) | 0 -> 0 (0) | **0 -> 7 (+7)** | **2 -> 9 (+7)** |
| Bielik-7B | Q4_K_M | 0 -> 0 (0) | 0 -> 0 (0) | 0 -> 0 (0) | 0 -> 0 (0) | **1 -> 3 (+2)** | **1 -> 3 (+2)** |
| Bielik-7B | Q3_K_M | 0 -> 0 (0) | 1 -> 1 (0) | 1 -> 1 (0) | 0 -> 0 (0) | 0 -> 0 (0) | 2 -> 2 (0) |
| Bielik-7B | Q2_K | 0 -> 0 (0) | 0 -> 0 (0) | 0 -> 0 (0) | 0 -> 0 (0) | 0 -> 0 (0) | 0 -> 0 (0) |

Delta jest niezerowa **wylacznie na L3N**, we wszystkich osmiu runach. Suma darowanych = 20.

#### 2.2 Te same komorki jako raty

| model | kwant | L0 | L1 | L2 | L3T | L3N scisla | L3N skoryg. | L3N delta | RAZEM scisla | RAZEM skoryg. | RAZEM delta |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Bielik-11B | Q8_0 | 0.00 -> 0.00 | 0.10 -> 0.10 | 0.40 -> 0.40 | 1.00 -> 1.00 | 0.20 | **0.90** | +0.70 | 0.283 | **0.435** | +0.152 |
| Bielik-11B | Q4_K_M | 0.00 -> 0.00 | 0.00 -> 0.00 | 0.10 -> 0.10 | 0.00 -> 0.00 | 0.00 | **0.40** | +0.40 | 0.022 | **0.109** | +0.087 |
| Bielik-11B | Q3_K_M | 0.00 -> 0.00 | 1.00 -> 1.00 | 1.00 -> 1.00 | 0.83 -> 0.83 | 0.70 | 0.70 | 0.00 | 0.696 | 0.696 | 0.000 |
| Bielik-11B | Q2_K | 0.00 -> 0.00 | 0.00 -> 0.00 | 0.00 -> 0.00 | 0.00 -> 0.00 | 0.00 | 0.00 | 0.00 | 0.000 | 0.000 | 0.000 |
| Bielik-7B | Q8_0 | 0.00 -> 0.00 | 0.00 -> 0.00 | 0.20 -> 0.20 | 0.00 -> 0.00 | 0.00 | **0.70** | +0.70 | 0.043 | **0.196** | +0.152 |
| Bielik-7B | Q4_K_M | 0.00 -> 0.00 | 0.00 -> 0.00 | 0.00 -> 0.00 | 0.00 -> 0.00 | 0.10 | **0.30** | +0.20 | 0.022 | **0.065** | +0.043 |
| Bielik-7B | Q3_K_M | 0.00 -> 0.00 | 0.10 -> 0.10 | 0.10 -> 0.10 | 0.00 -> 0.00 | 0.00 | 0.00 | 0.00 | 0.043 | 0.043 | 0.000 |
| Bielik-7B | Q2_K | 0.00 -> 0.00 | 0.00 -> 0.00 | 0.00 -> 0.00 | 0.00 -> 0.00 | 0.00 | 0.00 | 0.00 | 0.000 | 0.000 | 0.000 |

Raty na L0-L3T i raty RAZEM przepisane 1:1 z `ladder_breakdown.txt` (TABELA 1) i
`ladder_typing_tolerant.txt` (TABELA 3). Kolumny delta policzone z ulamkow dokladnych, np.
`20/46 - 13/46 = 7/46 = 0.152`, `9/46 - 2/46 = 7/46 = 0.152`, `5/46 - 1/46 = 4/46 = 0.087`,
`3/46 - 1/46 = 2/46 = 0.043`.

Zbiorczo po osmiu runach (moja arytmetyka na powyzszych osmiu wierszach, n = 8 x 46 = 368):
scisla **51/368 = 0.139**, skorygowana **71/368 = 0.193**, delta **20/368 = 0.054**.

#### 2.3 Ranking: co korekta zmienia w uporzadkowaniu kwantow

| pozycja | rata scisla | rata skorygowana |
|---|---|---|
| 1 | 11B Q3_K_M 0.696 | 11B Q3_K_M 0.696 |
| 2 | 11B Q8_0 0.283 | 11B Q8_0 0.435 |
| 3 | 7B Q8_0 0.043 = 7B Q3_K_M 0.043 | 7B Q8_0 0.196 |
| 4 | 11B Q4_K_M 0.022 = 7B Q4_K_M 0.022 | 11B Q4_K_M 0.109 |
| 5 | — | 7B Q4_K_M 0.065 |
| 6 | — | 7B Q3_K_M 0.043 |
| 7/8 | 11B Q2_K 0.000, 7B Q2_K 0.000 | 11B Q2_K 0.000, 7B Q2_K 0.000 |

Uporzadkowanie z tabeli 2.2. Q3 > Q8 na 11B i Q2 = 0.000 na obu modelach nie zmieniaja sie po
korekcie. Zmienia sie miejsce 7B Q3_K_M: przy racie scislej remisuje z 7B Q8_0 (oba 2/46), przy
skorygowanej spada za 7B Q8_0 (2/46 vs 9/46) i za 7B Q4_K_M (2/46 vs 3/46).

---

### 3. Lista zadan zmieniajacych werdykt po korekcie (20 sztuk)

Zrodlo: `scratchpad\sections\_helpers\typing_forgiven_list.py` — skrypt tylko-do-odczytu,
odtwarzajacy warunek `ladder_typing_tolerant.py:93-96` i wypisujacy dla kazdego darowanego zadania
`task_id`, typ i wartosc `answer`, golden, liczbe wywolan `convert_temperature` i tagi z `run.log`.
Wejscie: te same osiem katalogow `*_no_repair` + `tasks/ladder_ext/*.yaml`. Uruchomienie:
`cd /c/Users/japre/polagentbench && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe <sciezka>/typing_forgiven_list.py`.
Kolumna "wartosc" jest niezaleznie potwierdzona przez `analysis_out/ladder_nearmiss.txt` dla
czterech runow, ktore ten skrypt obejmuje (11B Q8, 11B Q4, 7B Q8, 7B Q4).

| # | model | kwant | task_id | szczebel | typ `answer` | wartosc `answer` | golden | konwersji | tagi z run.log |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Bielik-11B | Q8_0 | `v3_ext_L3N_b` | L3N | float | `48.2` | 48.2 / 48,2 | 2 | final_answer_missing, schema_violation |
| 2 | Bielik-11B | Q8_0 | `v3_ext_L3N_c` | L3N | float | `45.5` | 45.5 / 45,5 | 2 | final_answer_missing, schema_violation |
| 3 | Bielik-11B | Q8_0 | `v3_ext_L3N_e` | L3N | float | `46.4` | 46.4 / 46,4 | 2 | final_answer_missing, schema_violation |
| 4 | Bielik-11B | Q8_0 | `v3_ext_L3N_f` | L3N | float | `45.5` | 45.5 / 45,5 | 2 | final_answer_missing, schema_violation |
| 5 | Bielik-11B | Q8_0 | `v3_ext_L3N_g` | L3N | float | `35.6` | 35.6 / 35,6 | 2 | final_answer_missing, schema_violation |
| 6 | Bielik-11B | Q8_0 | `v3_ext_L3N_i` | L3N | float | `42.8` | 42.8 / 42,8 | 2 | final_answer_missing, schema_violation |
| 7 | Bielik-11B | Q8_0 | `v3_ext_L3N_j` | L3N | float | `43.7` | 43.7 / 43,7 | 2 | final_answer_missing, schema_violation |
| 8 | Bielik-11B | Q4_K_M | `v3_ext_L3N_a` | L3N | float | `46.4` | 46.4 / 46,4 | 2 | final_answer_missing, schema_violation |
| 9 | Bielik-11B | Q4_K_M | `v3_ext_L3N_b` | L3N | float | `48.2` | 48.2 / 48,2 | 2 | final_answer_missing, schema_violation |
| 10 | Bielik-11B | Q4_K_M | `v3_ext_L3N_e` | L3N | float | `46.4` | 46.4 / 46,4 | 2 | final_answer_missing, schema_violation |
| 11 | Bielik-11B | Q4_K_M | `v3_ext_L3N_h` | L3N | float | `41.9` | 41.9 / 41,9 | 2 | final_answer_missing, schema_violation |
| 12 | Bielik-7B | Q8_0 | `v3_ext_L3N_a` | L3N | dict | `{'average_fahrenheit': 46.4}` | 46.4 / 46,4 | 2 | final_answer_missing, invalid_json, schema_violation |
| 13 | Bielik-7B | Q8_0 | `v3_ext_L3N_b` | L3N | dict | `{'average_temperature_fahrenheit': 48.2}` | 48.2 / 48,2 | 2 | final_answer_missing, invalid_json, schema_violation |
| 14 | Bielik-7B | Q8_0 | `v3_ext_L3N_c` | L3N | dict | `{'average_temperature_fahrenheit': 45.5}` | 45.5 / 45,5 | 2 | final_answer_missing, invalid_json, schema_violation |
| 15 | Bielik-7B | Q8_0 | `v3_ext_L3N_d` | L3N | dict | `{'average_temperature_fahrenheit': 47.3}` | 47.3 / 47,3 | 2 | final_answer_missing, invalid_json, schema_violation |
| 16 | Bielik-7B | Q8_0 | `v3_ext_L3N_e` | L3N | dict | `{'average_temperature_fahrenheit': 46.4}` | 46.4 / 46,4 | 2 | final_answer_missing, invalid_json, schema_violation |
| 17 | Bielik-7B | Q8_0 | `v3_ext_L3N_f` | L3N | dict | `{'average_fahrenheit': 45.5}` | 45.5 / 45,5 | 2 | final_answer_missing, invalid_json, schema_violation |
| 18 | Bielik-7B | Q8_0 | `v3_ext_L3N_j` | L3N | dict | `{'average_temperature_f': 43.7}` | 43.7 / 43,7 | 2 | final_answer_missing, invalid_json, schema_violation |
| 19 | Bielik-7B | Q4_K_M | `v3_ext_L3N_e` | L3N | float | `46.4` | 46.4 / 46,4 | 2 | final_answer_missing, invalid_json, schema_violation |
| 20 | Bielik-7B | Q4_K_M | `v3_ext_L3N_i` | L3N | float | `42.8` | 42.8 / 42,8 | 2 | final_answer_missing, schema_violation |

Fakty z tej listy:

- Wszystkie 20 to **L3N**; zaden inny szczebel nie ma darowanego zadania.
- Wszystkie 20 maja **dokladnie 2 wywolania `convert_temperature`**, czyli lancuch wymagany przez
  `tools_called_in_order_strict` (`get_weather > get_forecast > convert_temperature x2`,
  `analysis_out/ladder_rungs.txt`).
- Wszystkie 20 maja zrodlo wartosci `SUROWY` (odzyskane z `raw_model_output`), zaden `SPARSOWANY`.
- Klucze slownikow u 7B Q8 nie sa staly: `average_fahrenheit` (2x),
  `average_temperature_fahrenheit` (4x), `average_temperature_f` (1x).
- Przyklad linii `run.log`, ktora produkuje wiersz 3 tej tabeli
  (`results/v3_11b_ladder_2026-07-29/q8_no_repair/run.log`, linia 38):
  `v3_ext_L3N_e  ✗  get_weather(city='Gliwice') -> get_forecast(city='Gliwice', days=4) -> convert_temperature(value=7.5, ...) -> convert_temperature(value=8.5, ...) -> parse_error[schema_violation] x4 - final_answer_missing, schema_violation`.

**Zadania blisko granicy, ktore NIE zostaly darowane** (`analysis_out/ladder_nearmiss.txt`, ten sam
ksztalt bledu, ale golden nieobecny — wiec korekta ich nie dotyka):

| model | kwant | task_id | typ | wartosc `answer` | golden |
|---|---|---|---|---|---|
| Bielik-11B | Q8_0 | `v3_ext_L3N_h` | float | `42.4` | 41.9 / 41,9 |
| Bielik-11B | Q4_K_M | `v3_ext_L3N_c` | float | `13.5` | (golden=NIE) |
| Bielik-11B | Q4_K_M | `v3_ext_L3N_d` | float | `13.5` | (golden=NIE) |
| Bielik-11B | Q4_K_M | `v3_ext_L3N_f` | float | `13.5` | (golden=NIE) |
| Bielik-11B | Q4_K_M | `v3_ext_L3N_g` | float | `35.3` | (golden=NIE) |
| Bielik-11B | Q4_K_M | `v3_ext_L3N_i` | float | `34.0` | (golden=NIE) |
| Bielik-11B | Q4_K_M | `v3_ext_L3N_j` | float | `13.5` | (golden=NIE) |
| Bielik-7B | Q8_0 | `v3_ext_L3N_h` | dict | `{'average_temperature_fahrenheit': 42.4}` | (golden=NIE) |
| Bielik-7B | Q8_0 | `v3_ext_L3N_i` | dict | `{'average_temperature_f': 43.3}` | (golden=NIE) |
| Bielik-7B | Q4_K_M | `v3_ext_L3N_b` | float | `61.5` | (golden=NIE) |
| Bielik-7B | Q4_K_M | `v3_ext_L3N_g` | float | `18.0` | (golden=NIE) + tagi trescowe `unknown_action`, `wrong_tool_order` |

`ladder_nearmiss.txt` podaje przy tych wierszach `golden=NIE` bez wypisania wartosci golden (poza
`L3N_h` na 11B Q8, gdzie z listy darowanych 11B Q4 wiadomo, ze golden dla instancji `h` to 41.9).
Wiersz `7B Q4 / L3N_g` jest jedynym w calym `ladder_nearmiss.txt`, ktory odpada takze na warunku
pierwszym (tagi trescowe), a nie tylko na golden.

---

### 4. Trzecia rata obecna w zrodle: "tolerancyjna SKROT"

Zrodlo: `analysis/ladder_typing_tolerant.py` -> `ladder_typing_tolerant.txt`, blok "Podsumowanie
L3N — trzy raty obok siebie", oraz `analysis/ladder_breakdown.py` -> `ladder_breakdown.txt`,
TABELA 2.

| model | kwant | L3N scisla | L3N tolerancyjna SKROT | L3N tolerancyjna TYPOWANIE |
|---|---|---|---|---|
| Bielik-11B | Q8_0 | 2/10 = 0.20 | 2/10 = 0.20 | 9/10 = 0.90 |
| Bielik-11B | Q4_K_M | 0/10 = 0.00 | 0/10 = 0.00 | 4/10 = 0.40 |
| Bielik-11B | Q3_K_M | 7/10 = 0.70 | 7/10 = 0.70 | 7/10 = 0.70 |
| Bielik-11B | Q2_K | 0/10 = 0.00 | 0/10 = 0.00 | 0/10 = 0.00 |
| Bielik-7B | Q8_0 | 0/10 = 0.00 | 0/10 = 0.00 | 7/10 = 0.70 |
| Bielik-7B | Q4_K_M | 1/10 = 0.10 | 1/10 = 0.10 | 3/10 = 0.30 |
| Bielik-7B | Q3_K_M | 0/10 = 0.00 | 0/10 = 0.00 | 0/10 = 0.00 |
| Bielik-7B | Q2_K | 0/10 = 0.00 | 0/10 = 0.00 | 0/10 = 0.00 |

Rata "SKROT" (golden obecny przy jednej konwersji zamiast dwoch) rowna sie scislej we wszystkich
osmiu runach, bo kategoria SKROT ma **0 przypadkow na 80 zadan L3N** (TABELA 2, kolumna SKROT = 0
w kazdym wierszu; kontrolne pelne wyliczenie L3N pod TABELA 2 sumuje sie do 10 w kazdym runie).

---

### 5. Kontrola: tolerancja nie rozdaje darmowych punktow na L1/L2

Zrodlo: `analysis/ladder_controls.py` -> `analysis_out/ladder_controls.txt`, blok "11B Q8: dlaczego
L1/L2 NIE zostaly darowane". Wejscie: `results/v3_11b_ladder_2026-07-29/q8_no_repair/{run.log,trajectories.jsonl}`
+ `tasks/ladder_ext/*.yaml`.

#### 5.1 Bilans L1 i L2 na 11B Q8

| szczebel | n | PASS | FAIL | FAIL z tagami wylacznie formatowymi | FAIL z golden obecnym | darowanych |
|---|---|---|---|---|---|---|
| L1 | 10 | 1 (`_f`) | 9 | 9 | 0 | **0** |
| L2 | 10 | 4 (`_a`, `_c`, `_d`, `_h`) | 6 | 6 | 0 | **0** |
| razem | 20 | 5 | 15 | **15 / 15** | **0 / 15** | **0** |

Liczby PASS/FAIL i przypisanie do zadan: `ladder_controls.txt` (kazdy z 20 wierszy podpisany PASS
albo `FAIL tagi=[...] -> golden BRAK (golden=..., model=...)`). Zliczenie 15/15 i 0/15 —
`_helpers/typing_forgiven_audit.py`, ostatni blok, linia
`porazek L1+L2 = 15, z tego tagi wylacznie formatu = 15, darowanych = 0`.

**To jest sedno kontroli:** wszystkie 15 porazek L1/L2 spelnia warunek 1 reguly (tagi to dokladnie
`['final_answer_missing', 'schema_violation']`) **i** warunek "nie-string" — a mimo to zero jest
darowanych, bo odpadaja na warunku golden. Typy pola `answer` w tych 15 porazkach
(`_helpers/typing_l1l2_types.py`): **9 x `int`, 6 x `float`**, zero stringow. Gdyby regula pomijala
test golden, korekta oddalaby na samym 11B Q8 dodatkowe 15 zadan (13 -> 35 z 46 zamiast 13 -> 20).

#### 5.2 Konkretne wartosci — golden nieobecny, "59 zamiast 46.4"

| task_id | golden | wartosc `answer` modelu | typ |
|---|---|---|---|
| `v3_ext_L1_a` | **46.4** / 46,4 | **59** | int |
| `v3_ext_L1_b` | 48.2 / 48,2 | 54.2 | float |
| `v3_ext_L1_c` | 45.5 / 45,5 | 51 | int |
| `v3_ext_L1_d` | 47.3 / 47,3 | 54.8 | float |
| `v3_ext_L1_e` | **46.4** / 46,4 | **59** | int |
| `v3_ext_L1_g` | 35.6 / 35,6 | 34.7 | float |
| `v3_ext_L1_h` | 41.9 / 41,9 | 59 | int |
| `v3_ext_L1_i` | 42.8 / 42,8 | 59 | int |
| `v3_ext_L1_j` | 43.7 / 43,7 | 59 | int |
| `v3_ext_L2_b` | 48.2 / 48,2 | 56.3 | float |
| `v3_ext_L2_e` | 46.4 / 46,4 | 52 | int |
| `v3_ext_L2_f` | 45.5 / 45,5 | 54.6 | float |
| `v3_ext_L2_g` | 35.6 / 35,6 | 50 | int |
| `v3_ext_L2_i` | 42.8 / 42,8 | 59 | int |
| `v3_ext_L2_j` | 43.7 / 43,7 | 51.2 | float |

Kolumny `golden` i `wartosc` sa w `ladder_controls.txt` (fraza `golden BRAK (golden=46.4, model=59)`
dla `L1_a` i `L1_e`). Kolumna `typ` — `_helpers/typing_l1l2_types.py`.
Wartosc **59** pada w **6 z 15** tych porazek (`L1_a`, `L1_e`, `L1_h`, `L1_i`, `L1_j`, `L2_i`);
histogram wszystkich wartosci: `{'59': 6, '54.2': 1, '51': 1, '54.8': 1, '34.7': 1, '56.3': 1,
'52': 1, '54.6': 1, '50': 1, '51.2': 1}`.

#### 5.3 Ta sama kontrola na wszystkich osmiu runach (nie tylko 11B Q8)

Zrodlo: `_helpers/typing_forgiven_audit.py`, pierwsza tabela. Rozklad **wszystkich 317 porazek** z
osmiu runow na cztery rozlaczne przyczyny:

| model | kwant | PASS | DAROWANE | odpadly: tagi formatowe, ale golden BRAK | odpadly: tagi formatowe + golden, ale `answer` jest stringiem | odpadly: tagi trescowe | n |
|---|---|---|---|---|---|---|---|
| Bielik-11B | Q8_0 | 13 | 7 | 16 | 0 | 10 | 46 |
| Bielik-11B | Q4_K_M | 1 | 4 | 22 | 0 | 19 | 46 |
| Bielik-11B | Q3_K_M | 32 | 0 | 3 | 0 | 11 | 46 |
| Bielik-11B | Q2_K | 0 | 0 | 1 | 0 | 45 | 46 |
| Bielik-7B | Q8_0 | 2 | 7 | 13 | 0 | 24 | 46 |
| Bielik-7B | Q4_K_M | 1 | 2 | 8 | 0 | 35 | 46 |
| Bielik-7B | Q3_K_M | 2 | 0 | 24 | 0 | 20 | 46 |
| Bielik-7B | Q2_K | 0 | 0 | 3 | 0 | 43 | 46 |
| **razem** | | **51** | **20** | **90** | **0** | **207** | **368** |

Kontrola sumy: 51 + 20 + 90 + 207 = 368; porazek 317 = 20 + 90 + 207; PASS 51 zgadza sie z suma
`num_passed` z `summary.json` osmiu runow (13+1+32+0+2+1+2+0).

Odczyt: **90 porazek** ma dokladnie ten sam profil bledu formatu co darowane, a mimo to nie dostaje
punktu, bo golden jest nieobecny — to 4,5-krotnie wiecej niz 20 darowanych. Kolumna
"golden + string" jest **zerowa w kazdym runie**, czyli w calej drabinie nie ma ani jednego
przypadku, w ktorym oracle odrzucilby poprawna odpowiedz podana jako string; korekta nie moze wiec
"na wszelki wypadek" ratowac czegokolwiek poza nie-stringami.

#### 5.4 Dlaczego L0 nie moze dostac ani jednego darowanego punktu

Zrodlo: `ladder_controls.txt`, blok "L0 = 0.00 we WSZYSTKICH 8 runach". L0 = 0.00 scisle i
skorygowanie w kazdym z osmiu runow (tabela 2.1).

| run | zliczenia tagow na 10 zadaniach L0 | wywolan narzedzi na zadanie |
|---|---|---|
| 11B Q8_0 | `unexpected_tool_call: 10`, `wrong_final_answer: 5`, `no_json_found: 1` | [1,2,2,2,1,2,2,2,2,2] |
| 11B Q3_K_M | `unexpected_tool_call: 10`, `wrong_final_answer: 5`, `no_json_found: 4` | [1,2,2,2,1,2,2,2,2,2] |
| 7B Q8_0 | `unknown_action: 10`, `wrong_final_answer: 1`, `final_answer_missing: 9`, `schema_violation: 3`, `invalid_json: 1` | [0]x10 |
| 11B Q2_K | `wrong_final_answer: 10` | [0]x10 |

Licznik zlicza po jednym na zadanie, wiec wartosc 10 oznacza "we wszystkich 10 zadaniach L0".
W 11B Q8 i 11B Q3 kazde zadanie L0 ma `unexpected_tool_call`, w 7B Q8 kazde ma `unknown_action`,
w 11B Q2 kazde ma `wrong_final_answer` — wszystkie te tagi sa **poza** `FMT_ONLY`, wiec warunek 1
reguly odpada na wejsciu. Przypadek 7B Q8 jest najostrzejszy: tagi formatowe **wystepuja** tam
(`final_answer_missing` 9, `schema_violation` 3, `invalid_json` 1), ale zawsze w towarzystwie
`unknown_action`, i test podzbioru `tg <= FMT_ONLY` je blokuje.

---

### 6. Rozszerzenia poza cztery pliki zrodlowe

Ponizsze dwie tabele **nie** pochodza z zadnego z 24 gotowych wyjsc — policzone skryptami
`_helpers/typing_forgiven_audit.py` i `_helpers/typing_forgiven_audit_repair.py`, ktore stosuja
regule `ladder_typing_tolerant.py:93-96` bez zmian do dodatkowych katalogow. Werdykty i tagi
czytane z `run.log`, wiec odtwarzanie oracle kodem HEAD nie zachodzi.

#### 6.1 PLLuM-8B na ladder46 — korekta nie zmienia nic

Wejscie: `results/v3_pllum_2026-07-29/q{2,3,4,5,6,8}_ladder_no_repair/{run.log,trajectories.jsonl}`
(commit e584b38, `run.log` = TAK wg `inventory.txt`, wiersze 91-102; seed=42, temp=0.0, n=46).

| model | kwant | L0 | L1 | L2 | L3T | L3N | RAZEM scisla | RAZEM skoryg. | darowanych |
|---|---|---|---|---|---|---|---|---|---|
| PLLuM-8B | Q2_K | 0/10 | 0/10 | 0/10 | 0/6 | 0/10 | 0/46 = 0.000 | 0/46 = 0.000 | 0 |
| PLLuM-8B | Q3_K_M | 0/10 | 0/10 | 0/10 | 0/6 | 0/10 | 0/46 = 0.000 | 0/46 = 0.000 | 0 |
| PLLuM-8B | Q4_K_M | 0/10 | 0/10 | 0/10 | 0/6 | 0/10 | 0/46 = 0.000 | 0/46 = 0.000 | 0 |
| PLLuM-8B | Q5_K_M | 0/10 | 0/10 | 0/10 | 0/6 | 0/10 | 0/46 = 0.000 | 0/46 = 0.000 | 0 |
| PLLuM-8B | Q6_K | 0/10 | 0/10 | 0/10 | 0/6 | 0/10 | 0/46 = 0.000 | 0/46 = 0.000 | 0 |
| PLLuM-8B | Q8_0 | 2/10 | 0/10 | 0/10 | 0/6 | 0/10 | 2/46 = 0.043 | 2/46 = 0.043 | 0 |

W szesciu runach PLLuM **zadna** porazka nie ma zestawu tagow zawartego w `FMT_ONLY`: rozklad
przyczyn to 46/46 "tagi trescowe" dla Q2-Q6 i 44/44 dla Q8. Korekta typowania jest zatem na tej
drabinie zjawiskiem wylacznie Bielikowym.

#### 6.2 Repair ON — te same osiem komorek Bielika

Wejscie: `results/v3_11b_ladder_2026-07-29/*_repair`, `results/v3_7b_ladder_2026-07-29/*_repair`.

| model | kwant | scisla (repair ON) | darowanych | skorygowana (repair ON) | dla porownania: skorygowana repair OFF |
|---|---|---|---|---|---|
| Bielik-11B | Q8_0 | 13/46 | 7 | 20/46 = 0.435 | 20/46 = 0.435 |
| Bielik-11B | Q4_K_M | 7/46 | 4 | 11/46 = 0.239 | 5/46 = 0.109 |
| Bielik-11B | Q3_K_M | 32/46 | 0 | 32/46 = 0.696 | 32/46 = 0.696 |
| Bielik-11B | Q2_K | 0/46 | 0 | 0/46 = 0.000 | 0/46 = 0.000 |
| Bielik-7B | Q8_0 | 3/46 | 8 | 11/46 = 0.239 | 9/46 = 0.196 |
| Bielik-7B | Q4_K_M | 9/46 | 2 | 11/46 = 0.239 | 3/46 = 0.065 |
| Bielik-7B | Q3_K_M | 2/46 | 0 | 2/46 = 0.043 | 2/46 = 0.043 |
| Bielik-7B | Q2_K | 0/46 | 0 | 0/46 = 0.000 | 0/46 = 0.000 |

Kolumna "scisla (repair ON)" zgadza sie z `inventory.txt` (wiersze 3-10 i 51-58: 13, 7, 32, 0, 3, 9,
2, 0). Przy repair ON pojawia sie jeden przypadek w kolumnie "golden + `answer` jest stringiem"
(7B Q8_0, 1 zadanie) — jedyny taki w calym materiale drabiny; przy repair OFF ta kolumna jest
wszedzie zerowa.

---

### 7. BRAK DANYCH i ograniczenia zasiegu

1. **BRAK DANYCH: drabina nie ma kwantow Q5_K_M i Q6_K dla Bielika.** `inventory.txt` zna dla
   ladder46 tylko `q2/q3/q4/q8` w `results/v3_11b_ladder_2026-07-29` i
   `results/v3_7b_ladder_2026-07-29`. Sensitivity typowania nie da sie wiec przelozyc 1:1 na
   szescio-kwantowa krzywa glowna main67 — brakuje dwoch z szesciu punktow dla obu Bielikow.
2. **BRAK DANYCH: korekta typowania nie zostala policzona dla suity main67.** Wszystkie cztery
   skrypty zrodlowe maja zaszyte katalogi drabiny. Czesc runow main67 (`v3_11b_2026-06-18`,
   `v3_arith_clean_2026-06-18`) **nie ma `run.log`**, a regula korekty czyta zestaw tagow wlasnie z
   `run.log`; odtworzenie tagow wymagaloby uruchomienia `eval.smoke.evaluate()` na tych
   trajektoriach, czego ta sekcja nie robi.
3. **Rata skorygowana nie jest werdyktem benchmarku.** Liczby z kolumn "skorygowana" powstaja z
   reguly zdefiniowanej w `analysis/ladder_typing_tolerant.py`, nie z ewaluatora
   `src/polagentbench/eval/smoke.py`. Zaden plik `summary.json` nie zawiera tych liczb.
4. Zliczenia w rozdziale 5.3 i 6 pochodza z moich skryptow pomocniczych, a nie z zapisanych wyjsc
   24 skryptow — sa odtwarzalne komenda podana w rozdziale 3, na tych samych plikach wejsciowych.
5. `analysis/README.md:64` ("float w 11B, dict w 7B") jest niedokladne dla 7B Q4_K_M — patrz
   rozdzial 1.3.

---


<!-- source section: 05_atraktor_wariancja.md -->

# Atraktor 59 i wariancja seedow

Repo: `C:\Users\japre\polagentbench`, HEAD `6c4f241`. Wszystkie liczby ponizej pochodza z plikow
na dysku (gotowe wyjscia skryptow w `scratchpad\analysis_out\`); zadnego runu modelu nie
uruchamiano.

Uwaga metodologiczna: `analysis/attractor59_scan_raw.py` (wyjscie `attractor59_scan_raw.txt`)
liczy KAZDY obiekt JSON osobno, a model powtarza te sama odpowiedz przez wiele krokow, wiec jego
liczby sa zawyzone (np. 61 wychodzi tam 4189 razy wobec 32 par run-zadanie, a 59 — 504 razy wobec
91 par) i NIE sa zrodlem zadnej liczby w tej sekcji; sluzy wylacznie jako material pomocniczy.

## Atraktor 59

### A1. Cztery zadania L1: model dostaje z narzedzia dokladnie golden i odpowiada 59

Skrypt zrodlowy: `analysis/attractor59_cases.py` → `analysis_out/attractor59_cases.txt`.
Pliki wejsciowe: `results/v3_11b_ladder_2026-07-29/q8_no_repair/trajectories.jsonl`,
`tasks/ladder_ext/v3_ext_*.yaml`.
Run: bielik-11b-v3 / Q8_0 / suite ladder46 / repair off / commit `e584b38` (wiersz 10 w
`analysis_out/inventory.txt`). To NIE jest komorka krzywej glownej main67 — material czytany
wylacznie z zapisanych trajektorii.

| task_id | golden | wartosci zwrocone przez `convert_temperature` [F] | srednia tych wartosci | odpowiedz modelu |
|---|---|---|---|---|
| v3_ext_L1_a (Łódź) | `46.4` / `46,4` | 45.5 (z 7.5 C), 47.3 (z 8.5 C) | 46.4 | 59 |
| v3_ext_L1_e (Gliwice) | `46.4` / `46,4` | 45.5 (z 7.5 C), 47.3 (z 8.5 C) | 46.4 | 59 |
| v3_ext_L1_h (Białystok) | `41.9` / `41,9` | 41.0 (z 5.0 C), 42.8 (z 6.0 C) | 41.9 | 59 |
| v3_ext_L1_i (Bielsko-Biała) | `42.8` / `42,8` | 41.9 (z 5.5 C), 43.7 (z 6.5 C) | 42.8 | 59 |

Ksztalt wszystkich czterech trajektorii jest identyczny (8 krokow, k0-k7):
k0 `get_forecast(city, days=4)`, k1 i k2 `convert_temperature` na dniu 2 i dniu 4,
k3-k7 piec razy ten sam obiekt `{"action": "final_answer", "answer": 59}`, za kazdym razem
odrzucony jako `parse_error[schema_violation]`, az do wyczerpania `max_steps`.

W kazdym z czterech przypadkow blok "GDZIE WYSTEPUJE '59' W WEJSCIU" w
`attractor59_cases.txt` daje: "NIGDZIE — ani w promptcie, ani w ograniczeniach, ani w zadnym
wyniku narzedzia".

59.0 = F(15.0 C) — kolumna `F->C` w `attractor59_count.txt`.

### A2. Zasieg: ile razy pada 59 w calym zbiorze wynikow

Skrypt zrodlowy: `analysis/attractor59_count.py` → `analysis_out/attractor59_count.txt`
(sekcja "=== 59: 91 par (run, zadanie) ===").
Pliki wejsciowe: `results/**/trajectories.jsonl`, `results/**/summary.json`.
Zliczanie: unikalne pary (run, zadanie), z deduplikacja powtorzen w obrebie jednej trajektorii.

| miara | wartosc |
|---|---|
| pary (run, zadanie) z odpowiedzia 59 | 91 |
| roznych zadan | 26 |
| roznych runow | 23 |
| roznych modeli | 2 |
| roznych poziomow kwantyzacji | 4 |

Poziomy kwantyzacji, na ktorych 59 wystapilo (rozklad model/kwant z tego samego pliku, suma
34+4+39+7+4+3 = 91):

| model | kwant | par (run, zadanie) |
|---|---|---|
| bielik-11b-v3 | Q8_0 | 39 |
| bielik-11b-v3 | Q4_K_M | 34 |
| bielik-11b-v3 | Q5_K_M | 4 |
| bielik-minitron-7b-v3 | Q3_K_M | 7 |
| bielik-minitron-7b-v3 | Q4_K_M | 4 |
| bielik-minitron-7b-v3 | Q5_K_M | 3 |

Wypisane poziomy kwantyzacji: **Q3_K_M, Q4_K_M, Q5_K_M, Q8_0** (cztery). Q2_K nie wystepuje;
llama-pllum-8b nie wystepuje — oba modele z lista to bieliki.

ROZBIEZNOSC DO ODNOTOWANIA: docstring `analysis/attractor59_count.py` mowi "oba modele, piec
poziomow kwantyzacji". Wyjscie tego samego skryptu pokazuje cztery poziomy (6 par model-kwant).
Liczba z danych to 4.

Dla kontekstu, 59.0 jest najczestsza liczbowa odpowiedzia w calym zbiorze; nastepne wartosci to
61 (32 pary / 7 zadan / 7 runow), 63 (28 / 12 / 10), 46.4 (27 / 9 / 17), 13.5 (26 / 9 / 4),
45.5 (26 / 11 / 19) — ta sama tabela w `attractor59_count.txt`.

26 zadan, w ktorych padlo 59 (lista z `attractor59_count.txt`): v3_arith_L1_a, v3_arith_L1_b,
v3_arith_L1_c, v3_arith_L3_a, v3_arith_L3_c, v3_chain_001, v3_chain_002, v3_chain_004,
v3_chain_004_arith, v3_chain_005, v3_chain_010, v3_ext_L1_a, v3_ext_L1_b, v3_ext_L1_c,
v3_ext_L1_d, v3_ext_L1_e, v3_ext_L1_h, v3_ext_L1_i, v3_ext_L1_j, v3_ext_L2_b, v3_ext_L2_d,
v3_ext_L2_e, v3_ext_L2_f, v3_ext_L2_h, v3_ext_L2_i, v3_ext_L2_j.

### A3. Kontrole negatywne

Skrypt zrodlowy: `analysis/attractor59_negative_controls.py` →
`analysis_out/attractor59_negative_controls.txt`.
Pliki wejsciowe: `tasks/**/*.yaml`, `src/polagentbench/environments/weather.py`,
`results/**/trajectories.jsonl`.

| kontrola | wynik |
|---|---|
| zadania z goldenem 59 / 59.0 / 59,0 | **0** — na 119 sprawdzonych zadan |
| zadania z goldenem 61 | 0 |
| zadania z goldenem 63 | 0 |
| liczba 59 (jako liczba calkowita) w `environments/weather.py` | NIE wystepuje |
| wartosc 15.0 wsrod temperatur srodowiska | NIE wystepuje |
| zakres temperatur w `weather.py` | od -5.0 do 19.0 C, 23 rozne wartosci |
| z 91 trajektorii z odpowiedzia 59: majace 59 w PROMPCIE | 0 |
| z 91 trajektorii z odpowiedzia 59: majace 59 w WYNIKU NARZEDZIA | 11 |

n = 119 sprawdzonych zadan: skrypt skanuje `tasks/**/*.yaml` i bierze kazdy plik z kluczem
`expected_final_state`. Liczbe 119 potwierdzilem osobnym przeliczeniem tego samego globu:
119 plikow yaml, wszystkie 119 maja `expected_final_state`; rozklad po katalogach:
`tasks/adversarial` 67 (= main67), `tasks/ladder_ext` 46 (= ladder46), `tasks/smoke` 5,
`tasks/_examples` 1. Czyli zakres kontroli jest szerszy niz sama suita main67.

Pelna lista temperatur zmiennoprzecinkowych znalezionych w `weather.py`:
-5.0, 0.5, 2.0, 3.0, 4.0, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 11.0, 12.0,
14.0, 16.0, 17.0, 18.0, 19.0.

Najczestsze goldeny w suicie (kontekst, ten sam plik): 46.4 i 46,4 po 16 zadan, 45.5 i 45,5 po
16, 48.2 i 48,2 po 10, 47.3 i 47,3 po 7, 35.6 i 35,6 po 4.

### A4. Kierunek: 59 nie przychodzi z kontekstu, model wymusza je na narzedziu

Skrypt zrodlowy: `analysis/attractor59_direction.py` → `analysis_out/attractor59_direction.txt`.
Plik wejsciowy: `results/**/trajectories.jsonl`.

Potwierdzenie liczb: plik konczy sie linia "znalezionych: 11" i zawiera dokladnie 11 wierszy.
We WSZYSTKICH 11 przypadkach argument podany narzedziu przez model to
`convert_temperature({"value": 15, "from_unit": "celsius", "to_unit": "fahrenheit"})`, a wynik
narzedzia to `{"value": 59.0, ...}`. Nie ma ani jednego wiersza z innym argumentem.

Zestawienie kierunku (z A3 i A4):

| | liczba z 91 |
|---|---|
| 59 obecne w promptcie zadania | 0 |
| 59 obecne w wyniku narzedzia | 11 |
| z tych 11: 59 pojawilo sie dlatego, ze model sam podal `value=15` | 11 z 11 |

Wykaz 11 przypadkow (run / zadanie / krok, z `attractor59_direction.txt`):

| run | zadanie | krok |
|---|---|---|
| v3_11b_ladder_2026-07-29\q4_no_repair | v3_ext_L2_e | k2 |
| v3_11b_ladder_2026-07-29\q4_repair | v3_ext_L2_e | k2 |
| v3_11b_ladder_2026-07-29\q8_no_repair | v3_ext_L2_b | k2 |
| v3_11b_ladder_2026-07-29\q8_repair | v3_ext_L2_b | k2 |
| v3_full_2026-06-02\Q3_K_M | v3_chain_005 | k3 |
| v3_full_2026-06-02\q3_no_repair | v3_chain_005 | k3 |
| v3_full_2026-06-02\q3_repair | v3_chain_005 | k3 |
| v3_ladder_2026-06-11\q3_no_repair | v3_arith_L3_c | k3 |
| v3_ladder_2026-06-11\q3_no_repair | v3_chain_005 | k3 |
| v3_ladder_2026-06-11\q3_repair | v3_arith_L3_c | k3 |
| v3_ladder_2026-06-11\q3_repair | v3_chain_005 | k3 |

15.0 C nie wystepuje w danych srodowiska (A3), wiec liczba 15 podana narzedziu rowniez nie
pochodzi z wejscia.

## Wariancja seedow

Wszystkie runy tej czesci: `results/v3_11b_variance_2026-07-29/{q8,q3}_seed{1,2,3}`,
model bielik-11b-v3, suite main67 (67 zadan), repair off, commit `e584b38`, `run.log` obecny
(wiersze 15-17 i 26-28 w `analysis_out/inventory.txt`). Werdykty w tabelach B2-B3 pochodza
z `run.log` (oracle), a nie z `trajectory.success`.

### B1. Konfiguracja: gdzie zapisany jest seed

Skrypt zrodlowy: `analysis/variance_seed_config.py` → `analysis_out/variance_seed_config.txt`,
blok A. Pliki wejsciowe:
`results/v3_11b_variance_2026-07-29/{q8,q3}_seed{1,2,3}/{summary.json,trajectories.jsonl}`.

| katalog | summary.seed | summary.temperature | seed w rekordach trajektorii | temperatura w rekordach trajektorii | zdane |
|---|---|---|---|---|---|
| q8_seed1 | None | None | [1] | [0.7] | 8/67 |
| q8_seed2 | None | None | [2] | [0.7] | 49/67 |
| q8_seed3 | None | None | [3] | [0.7] | 48/67 |
| q3_seed1 | None | None | [1] | [0.7] | 13/67 |
| q3_seed2 | None | None | [2] | [0.7] | 43/67 |
| q3_seed3 | None | None | [3] | [0.7] | 51/67 |

- Temperatura: T = 0.7 we wszystkich szesciu runach, jedna wartosc na run (kolumna "temp w traj.").
- Seedy: 1, 2, 3 — po jednej wartosci na run, zgodnej z nazwa katalogu.
- Gdzie zapisany: `summary.json` NIE MA kluczy `seed` ani `temperature` (sprawdzone bezposrednio:
  `'seed' in summary == False`, `'temperature' in summary == False` dla wszystkich szesciu
  plikow; skrypt drukuje `None`, bo uzywa `.get`). Obie wartosci sa w rekordach trajektorii,
  czyli w `trajectories.jsonl`, jako pola `seed` i `temperature` obiektu `Trajectory`
  (`src/polagentbench/types.py:208` — pole `seed: int`).
- Konsekwencja: przypisanie runu do seeda po nazwie katalogu jest potwierdzone niezaleznie danymi
  z trajektorii.

### B2. Wyniki per seed (11B, main67)

Skrypt zrodlowy: `analysis/variance_seed_config.py` → `analysis_out/variance_seed_config.txt`
(kolumna "passed"); wartosci `success_rate` odczytane bezposrednio z
`results/v3_11b_variance_2026-07-29/*/summary.json`.

| kwant | seed | zdane / 67 | rate |
|---|---|---|---|
| Q8_0 | 1 | 8/67 | 0.1194 |
| Q8_0 | 2 | 49/67 | 0.7313 |
| Q8_0 | 3 | 48/67 | 0.7164 |
| Q3_K_M | 1 | 13/67 | 0.1940 |
| Q3_K_M | 2 | 43/67 | 0.6418 |
| Q3_K_M | 3 | 51/67 | 0.7612 |

Te same liczby zdanych wychodza niezaleznie z `run.log` (kolumna PASS w
`analysis_out/variance_classify.txt`): 8, 49, 48, 13, 43, 51 — zgodne z `summary.num_passed`.

Ksztalt runu seed1 wobec pozostalych (Q8_0), z bloku B `variance_seed_config.txt`
(wejscie: `trajectories.jsonl`):

| miara | seed1 | seed2 | seed3 |
|---|---|---|---|
| trajektorii | 67 | 67 | 67 |
| krokow | 319 | 293 | 329 |
| krokow / trajektorie | 4.76 | 4.37 | 4.91 |
| trajektorii 0-krokowych | 0 | 0 | 0 |
| pustych wyjsc | 0 | 0 | 0 |
| call_tool | 129 | 192 | 204 |
| final_answer | 49 | 63 | 57 |
| krokow sparsowanych OK | 178 | 255 | 261 |
| trajektorii na max_steps (8) | 16 | 5 | 11 |
| mediana dlugosci wyjscia [zn.] | 133 | 132 | 132 |
| tokenow | 472 692 | 419 324 | 485 201 |
| czas [s] | 417 | 274 | 309 |

### B3. Tabela 2c — sufity po darowaniu bledow formatu

Skrypt zrodlowy: `analysis/variance_classify.py` → `analysis_out/variance_classify.txt`.
Pliki wejsciowe: `results/v3_11b_variance_2026-07-29/*/{run.log,trajectories.jsonl}`.
Klasyfikacja porazek po tagach z `run.log`: A = same tagi formatu, B = tagi formatu i tresci
razem (kaskada), C = same tagi tresci.

| run | PASS | A czysty format | B kaskada fmt+tresc | C twarda tresc | sufit ostrozny (A darowane) | sufit hojny (A+B) |
|---|---|---|---|---|---|---|
| q8_seed1 | 8/67 | 14 | 30 | 15 | 22/67 = 0.328 | **52/67 = 0.776** |
| q8_seed2 | 49/67 | 6 | 6 | 6 | 55/67 = 0.821 | 61/67 = 0.910 |
| q8_seed3 | 48/67 | 7 | 9 | 3 | 55/67 = 0.821 | 64/67 = 0.955 |
| q3_seed1 | 13/67 | 17 | 29 | 8 | 30/67 = 0.448 | **59/67 = 0.881** |
| q3_seed2 | 43/67 | 7 | 5 | 12 | 50/67 = 0.746 | 55/67 = 0.821 |
| q3_seed3 | 51/67 | 6 | 5 | 5 | 57/67 = 0.851 | 62/67 = 0.925 |

POTWIERDZONE: seed1 po darowaniu kaskad formatu (kolumna A+B) daje 52/67 = 0.776 dla Q8_0
i 59/67 = 0.881 dla Q3_K_M. Wartosci przeliczone niezaleznie: 52/67 = 0.7761, 59/67 = 0.8806.
Faktyczne (niedarowane) wyniki seedow 2 i 3 to 0.7313 / 0.7164 (Q8) i 0.6418 / 0.7612 (Q3).

Udzial krokow, ktore sie nie parsuja (drugi blok tego samego pliku, wejscie `trajectories.jsonl`):

| run | krokow | bledy parsowania | udzial | traj. na max_steps |
|---|---|---|---|---|
| q8_seed1 | 319 | 141 | 44.2% | 16 |
| q8_seed2 | 293 | 38 | 13.0% | 5 |
| q8_seed3 | 329 | 68 | 20.7% | 11 |
| q3_seed1 | 317 | 128 | 40.4% | 11 |
| q3_seed2 | 279 | 20 | 7.2% | 7 |
| q3_seed3 | 308 | 15 | 4.9% | 8 |

### B4. Dwumodalnosc — rozstep miedzy seedami

Wyliczone z liczb w B2 (`summary.json` / `run.log`), ten sam plik wejsciowy:

| kwant | najnizszy seed | najwyzszy seed | rozstep w zadaniach | rozstep w punktach procentowych | rozstep w rate |
|---|---|---|---|---|---|
| Q8_0 | seed1: 8/67 (0.1194) | seed2: 49/67 (0.7313) | 41 zadan | 61.2 pp | 0.6119 |
| Q3_K_M | seed1: 13/67 (0.1940) | seed3: 51/67 (0.7612) | 38 zadan | 56.7 pp | 0.5672 |

Rozstep miedzy seedami 2 i 3 (z pominieciem seed1): Q8_0 — 1 zadanie (49 vs 48, 1.5 pp);
Q3_K_M — 8 zadan (51 vs 43, 11.9 pp). Caly rozstep siedzi wiec miedzy seed1 a reszta,
w obu kwantach.

Po darowaniu kaskad formatu (B3, kolumna A+B) rozstep spada: Q8_0 z 0.776 (seed1) do
0.955 (seed3) = 12 zadan; Q3_K_M z 0.881 (seed1) do 0.925 (seed3) = 3 zadania.

### B5. Hipoteza zaklinowanego samplera — OBALONA

Skrypt zrodlowy: `analysis/variance_repetition.py` → `analysis_out/variance_repetition.txt`,
blok D. Pliki wejsciowe:
`results/v3_11b_variance_2026-07-29/*/{run.log,trajectories.jsonl}`.
Miara: udzial krokow bedacych doslownym powtorzeniem wczesniejszego `raw_model_output`
w tej samej trajektorii.

| run | traj. z powtorzonym wyjsciem (>=2 te same) | max powtorzen tego samego | krokow bedacych powtorka | udzial | wynik runu |
|---|---|---|---|---|---|
| q8_seed1 | 10 | 6 | 20 | **6.3%** | 8/67 |
| q8_seed2 | 6 | 7 | 19 | **6.5%** | 49/67 |
| q8_seed3 | 11 | 6 | 45 | **13.7%** | 48/67 |
| q3_seed1 | 14 | 4 | 31 | 9.8% | 13/67 |
| q3_seed2 | 4 | 3 | 7 | 2.5% | 43/67 |
| q3_seed3 | 5 | 3 | 11 | 3.6% | 51/67 |

POTWIERDZONE: liczby 6.3% / 6.5% / 13.7% zgadzaja sie co do cyfry z plikiem — to wiersze
q8_seed1 / q8_seed2 / q8_seed3. Run z NAJWIEKSZYM udzialem powtorzen (q8_seed3, 13.7%) ma
48/67 zdanych, a run z najgorszym wynikiem (q8_seed1, 8/67) ma 6.3%, czyli ponad dwa razy mniej
powtorzen. Kierunek jest wiec odwrotny do przewidywania hipotezy o zaklinowanym samplerze.

DOPRECYZOWANIE (dane mowia troche inaczej niz sformulowanie "seed3 = najlepszy wynik"):
w kwancie Q8_0 najlepszy jest seed2 (49/67), seed3 jest drugi o jedno zadanie (48/67).
Zdanie "seed3 najlepszy" jest doslownie prawdziwe dla Q3_K_M (51/67 — najlepszy wynik ze
wszystkich szesciu runow) oraz dla obu kwantow w slabszej formie "seed3 punktuje w gornym pasmie".
Wniosek o obaleniu hipotezy nie zmienia sie: 13.7% powtorzen towarzyszy 48/67, a 6.3% — 8/67.

Dla porownania z ta sama rodziny liczb: q3_seed1 ma 9.8% powtorzen przy 13/67, a q3_seed3
3.6% przy 51/67 — czyli w Q3_K_M kierunek jest zgodny z hipoteza, w Q8_0 przeciwny.
Miara nie rozdziela runow udanych od nieudanych w sposob spojny.

Blok E tego samego pliku: zadan PASS w seed2 i seed3 przy FAIL w seed1 (Q8_0) jest **38 z 67**;
tagi seed1 na tych zadaniach: wrong_tool_order 29, unknown_action 22, wrong_final_answer 8,
final_answer_missing 7, no_json_found 4, expected_tool_not_called 2. Przyklady w pliku
(adv_001, adv_003, adv_004a) pokazuja te sama tresc odpowiedzi co seed2, z jednym nadmiarowym
krokiem bez JSON-a albo z nazwa narzedzia wpisana rowniez w pole `action`.

### B6. Fakt o kodzie: seed jest podawany przy KAZDYM kroku

Plik: `src/polagentbench/inference/llama_cpp_runner.py`.

- Linia 102: `for step_idx in range(task.max_steps):` — petla po krokach wewnatrz jednej
  trajektorii.
- Linia 103: `original_text, latency_ms, usage = complete_chat(messages, seed)` — ten sam
  `seed` jest przekazywany do modelu w kazdej iteracji petli, a nie raz na trajektorie.
- Linie 302-311: `def _complete_chat(self, messages, seed)` woła
  `llm.create_chat_completion(messages=..., temperature=..., top_p=..., max_tokens=...,
  seed=seed)` — linia 311 to `seed=seed,` w wywolaniu llama.cpp.
- Skad seed bierze sie w petli: `LlamaCppRunner.run_task(task, seed)` przekazuje go do
  `agent_loop(...)` w linii 270; `agent_loop` ma parametr `seed: int` i nigdzie go nie modyfikuje.
- Gdzie seed zostaje zapisany: linia 178, `seed=seed,` w `return Trajectory(...)` — stad pole
  `seed` w `trajectories.jsonl` (B1). W tym samym konstruktorze, linia 185: `temperature=temperature,`.
- Przy okazji, ta sama konstrukcja pokazuje, dlaczego `trajectory.success` nie jest oracle'em:
  linia 181 to `success=final_answer_emitted`, czyli flaga mowi tylko, ze model w ogole wypuscil
  `final_answer`, bez porownania z goldenem.

Znaczenie dla pomiaru: przy `max_steps = 8` jeden seed wchodzi do samplera do osmiu razy
w obrebie jednej trajektorii, za kazdym razem z dluzszym kontekstem (historia wiadomosci rosnie
o kolejne wyjscia i wyniki narzedzi). Numer seeda jest wiec stala runu, a nie identyfikatorem
pojedynczego losowania.

## BRAK DANYCH

1. **Dlaczego akurat 59 / 15 C** — nie da sie ustalic z danych na dysku. Rekordy trajektorii
   (`TrajectoryStep`: `latency_ms`, `parse_error`, `parsed_action`, `raw_model_output`,
   `raw_model_output_pre_repair`, `repair_applied`, `state_after`, `step_idx`, `tool_result`)
   nie zawieraja logprobow ani rozkladow tokenow, a ustalenie mechanizmu wymagaloby nowego
   przebiegu modelu (zabronione w tym zadaniu).
2. **Czy 59 wystepowalo takze u llama-pllum-8b** — w rozkladzie 91 par nie ma ani jednego
   wpisu PLLuM. Z tych plikow nie wynika, czy to wlasnosc modelu, czy zakresu runow; skrypt
   liczy tylko to, co padlo, i nie raportuje mianownika (ile par run-zadanie danego modelu
   w ogole wyprodukowalo liczbowa odpowiedz).
3. **Wariancja seedow dla Q2/Q4/Q5/Q6 i dla pozostalych dwoch modeli** — na dysku jest tylko
   `v3_11b_variance_2026-07-29` z szescioma runami (Q8_0 i Q3_K_M, bielik-11b-v3). Innych
   siatek seedowych nie ma.
4. **Istotnosc statystyczna rozstepu miedzy seedami** — trzy seedy na kwant to za malo, zeby
   podac przedzial ufnosci; w plikach nie ma tez powtorzen tego samego seeda, wiec nie da sie
   oddzielic wariancji seeda od wariancji uruchomienia (niedeterminizm GPU).
5. **`summary.json` runow wariancyjnych nie zapisuje seeda ani temperatury** (kluczy po prostu
   nie ma). Kazde przypisanie runu do seeda musi isc przez `trajectories.jsonl`; gdyby nazwy
   katalogow byly jedynym zrodlem, nie dalo by sie tego zweryfikowac.
6. **Rozbieznosc do sprostowania w papierze**: docstring `analysis/attractor59_count.py` mowi
   o pieciu poziomach kwantyzacji, dane pokazuja cztery (Q3_K_M, Q4_K_M, Q5_K_M, Q8_0).

---


<!-- source section: 07_rozjazdy.md -->

## Rozjazdy: liczby w .tex vs przeliczone

### 0. Zakres i ograniczenie metodyczne

Sprawdzany plik: `C:\Users\japre\Desktop\results_section.tex` (143 linie, nagłówek komentarza: „Canonical run: commit 1b1af70, T=0, single seed, 2026-06-02").

Papieru docelowego („The Q2 Cliff…") nie ma na dysku jako `.tex` — poniższa lista dotyczy WYŁĄCZNIE starego fragmentu draftu.

**Ograniczenie (obowiązuje w całej sekcji):** run stemplowany commitem `1b1af70` NIE jest bajt w bajt zgodny z HEAD (`6c4f241`) dla `tasks/adversarial`:

```
git diff --stat 1b1af70 HEAD -- tasks/adversarial src/polagentbench/eval
-> 49 files changed, 2906 insertions(+), 21 deletions(-)
git diff --stat 1b1af70 HEAD -- src/polagentbench/eval
-> PUSTO (0 zmian)
```

Zmiany w `tasks/adversarial` to 45 plików NOWYCH + **4 pliki ZMODYFIKOWANE, i wszystkie 4 należą do kanonicznej dwudziestkidwójki**: `v3_chain_001.yaml` (7 linii), `v3_chain_001_arith.yaml` (15), `v3_chain_en_001.yaml` (11), `v3_chain_en_001_arith.yaml` (18). Dlatego **nie odtwarzam żadnego werdyktu kodem HEAD**. Wszystkie liczby poniżej pochodzą z zapisanych artefaktów runu:

| plik wejściowy | co z niego biorę |
|---|---|
| `results/v3_run_2026-06-02_22task/{Q8_0,Q4_K_M,Q2_K}/summary.json` | `num_passed`, `success_rate`, `failure_tag_counts`, `commit_hash` |
| `results/v3_run_2026-06-02_22task/{...}/trajectories.jsonl` | `seed`, `temperature`, treść `final_answer`, liczba kroków |
| `results/v3_run_2026-06-02_22task/DEGRADATION.md` | macierz per-task, podział easy/hard, tabela `_arith` struct/num |
| `results/v3_run_2026-06-02_22task/SENSITIVITY.md` | goldeny, sparsowane wartości, sweep tolerancji, lista flipów |
| `results/v3_run_2026-06-02_22task/ROBUSTNESS.md` | macierz per-task (appendix), CI bootstrap, rozbicie easy/hard |
| `results/v3_run_2026-06-02_22task/VALIDATION.md` | goldeny °F pozostałych zadań (kontrola krzyżowa) |
| `SESSION_LOG.md` (repo root) | rozmiary plików GGUF, BPW |
| `scratchpad/analysis_out/inventory.txt` (skrypt `analysis/inventory.py`) | wiersze `main22` |
| `git show 1b1af70:tasks/adversarial/*.yaml` | goldeny i specyfikacje zadań w brzmieniu z dnia runu |

**Pułapka odnotowana:** pole `trajectory.success` w `trajectories.jsonl` NIE jest oracle'em również dla tego runu. Zliczenie `success==True` daje **18 / 21 / 16** zamiast **17 / 19 / 9**, a `failure_tags` w trajektoriach zawierają wyłącznie tag `TIMEOUT` (4 / 1 / 6) — nie zawierają `unknown_action`, `schema_violation` itd., które są w `summary.json`. Werdykty per-task są odtwarzalne tylko z `DEGRADATION.md` / `ROBUSTNESS.md`.

---

### 1. Tabela `tab:gradient` (linie 29–43 .tex)

Źródło przeliczenia: `summary.json` ×3 + `DEGRADATION.md` §1 + `ROBUSTNESS.md` (C).

| wartość w .tex | linia .tex | wartość przeliczona | źródło przeliczenia | werdykt |
|---|---|---|---|---|
| Q8_0 `17/22` | 35 | 17/22 | `Q8_0/summary.json` `num_passed=17`, `num_total=22` | ZGODNE |
| Q8_0 `0.773` | 35 | 0.7727 | `Q8_0/summary.json` `success_rate=0.7727` | ZGODNE (zaokrąglenie) |
| Q8_0 easy `14/15` | 35 | 14/15 | `DEGRADATION.md` §1 tier-table; `ROBUSTNESS.md` appendix (suma kolumny Q8 dla 15 wierszy `E`) | ZGODNE |
| Q8_0 hard `3/7` | 35 | 3/7 | jw. (7 wierszy `H`) | ZGODNE |
| Q4_K_M `19/22` | 36 | 19/22 | `Q4_K_M/summary.json` `num_passed=19` | ZGODNE |
| Q4_K_M `0.864` | 36 | 0.8636 | `Q4_K_M/summary.json` `success_rate=0.8636` | ZGODNE (zaokrąglenie) |
| Q4_K_M Δ `+0.091` | 36 | +0.0909 (0.8636 − 0.7727) | `DEGRADATION.md` §1 kolumna „Δ vs Q8_0" | ZGODNE (zaokrąglenie) |
| Q4_K_M easy `15/15` | 36 | 15/15 | `DEGRADATION.md` §1; `ROBUSTNESS.md` (C) | ZGODNE |
| Q4_K_M hard `4/7` | 36 | 4/7 | jw. | ZGODNE |
| Q2_K `9/22` | 37 | 9/22 | `Q2_K/summary.json` `num_passed=9` | ZGODNE |
| Q2_K `0.409` | 37 | 0.4091 | `Q2_K/summary.json` `success_rate=0.4091` | ZGODNE (zaokrąglenie) |
| Q2_K Δ `−0.364` | 37 | −0.3636 (0.4091 − 0.7727) | `DEGRADATION.md` §1 | ZGODNE (zaokrąglenie) |
| Q2_K easy/hard: `collapse` (słowo, brak liczb) | 37 | easy **8/15** (0.533), hard **1/7** (0.143) | `DEGRADATION.md` §1 tier-table; `ROBUSTNESS.md` (C) | **BRAK LICZBY w .tex — dane istnieją** (rozjazd nr 1) |
| „drops 36 points" | 26 | 36.36 pp | 0.7727 − 0.4091 | ZGODNE (zaokrąglenie do pełnych punktów) |
| „collapses by 36 points" | 41 | 36.36 pp | jw. | ZGODNE (zaokrąglenie) |

Suma kontrolna: 14+3 = 17 ✓, 15+4 = 19 ✓, 8+1 = 9 ✓ (`ROBUSTNESS.md` appendix, wiersz **total** 17/19/9).

---

### 2. Tabela `tab:tags` (linie 55–73 .tex)

Źródło przeliczenia: `failure_tag_counts` z trzech `summary.json`; kontrola krzyżowa `DEGRADATION.md` §4.

| tag (linia .tex) | w .tex Q8/Q4/Q2 | przeliczone Q8/Q4/Q2 | źródło | werdykt |
|---|---|---|---|---|
| `unknown_action` (61) | 12 / 1 / 17 | 12 / 1 / 17 | `summary.json` ×3 | ZGODNE |
| `final_answer_missing` (62) | 5 / 1 / 7 | 5 / 1 / 7 | jw. | ZGODNE |
| `wrong_tool_order` (63) | 2 / 1 / 5 | 2 / 1 / 5 | jw. | ZGODNE |
| `timeout` (64) | 4 / 1 / 6 | 4 / 1 / 6 | jw. | ZGODNE |
| `schema_violation` (65) | 4 / 5 / 0 | 4 / 5 / brak klucza (=0) | jw. | ZGODNE |
| `expected_tool_not_called` (66) | 0 / 0 / 6 | brak klucza (=0) / brak klucza (=0) / 6 | jw. | ZGODNE |
| to samo w tekście: `0/0/6`, `2/1/5`, `4/5/0` | 48, 49, 50 | jw. | jw. | ZGODNE |

**Czego w tabeli .tex NIE MA, a jest w danych** (rozjazd nr 2) — cztery tagi pominięte:

| tag pominięty w .tex | Q8_0 | Q4_K_M | Q2_K | źródło |
|---|---|---|---|---|
| `final_answer_shape_violation` | 1 | 0 | 0 | `summary.json`, `DEGRADATION.md` §4 |
| `invalid_json` | 1 | 0 | 0 | jw. |
| `wrong_final_answer` | 1 | 2 | 2 | jw. |
| `unexpected_tool_call` | 0 | 0 | 1 | jw. |

Skutek liczbowy: suma kolumny w tabeli .tex = **27 / 9 / 41**, suma wszystkich tagów w `summary.json` = **30 / 11 / 44**.

---

### 3. Tabela `tab:arith` + sweep tolerancji (linie 87–128 .tex)

Źródło przeliczenia: `SENSITIVITY.md` §A (goldeny, sparsowane liczby, sweep), `DEGRADATION.md` §3, oraz odczyt `final_answer` wprost z `trajectories.jsonl`.

| wartość w .tex | linia | przeliczone | źródło | werdykt |
|---|---|---|---|---|
| golden `45.97` (`001_arith`) | 112 | 45.97 | `git show 1b1af70:tasks/adversarial/v3_chain_001_arith.yaml` → `final_answer_contains_any: ["45.97","45,97"]`; `SENSITIVITY.md` §A | ZGODNE (dla commita 1b1af70) |
| golden `49.57` (`en_001_arith`) | 117 | 49.57 | `git show 1b1af70:…/v3_chain_en_001_arith.yaml` → `["49.57","49,57"]` | ZGODNE (dla commita 1b1af70) |
| `47.24` @Q8 | 96, 113 | 47.24 | `Q8_0/trajectories.jsonl`, `v3_chain_001_arith`: „…wynosi 7.8°C, co odpowiada **47.24**°F." | ZGODNE |
| `+1.27` | 96, 113 | 47.24 − 45.97 = 1.27 | wyliczenie; `SENSITIVITY.md`: „1.27 off" | ZGODNE |
| `---` (no-number, placeholder) @Q4 dla `001_arith` | 97, 114 | `final_answer='średnia_temperatura_w_fahrenheit'`, liczb = `[]` | `Q4_K_M/trajectories.jsonl`; `SENSITIVITY.md` „no-number" | ZGODNE |
| `59.0` @Q2 | 98, 115 | 59.0 | `Q2_K/trajectories.jsonl`: „…wynosi 15.0°C, co w przeliczeniu na Fahrenheit wynosi **59.0**°F." | ZGODNE |
| `+13.0` | 115 | 59.0 − 45.97 = **13.03** | wyliczenie; `SENSITIVITY.md`: „13.03 off" | **ROZJAZD (drobny, zaokrąglenie)** — rozjazd nr 3 |
| „mean 15 °C" | 98, 115 | 15.0 | `Q2_K/trajectories.jsonl`, liczby w odpowiedzi `[15.0, 59.0]` | ZGODNE |
| `---` (empty) @Q8 dla `en_001_arith` | 99, 118 | `final_answer = None` (brak kroku `final_answer`, 8 kroków = max_steps) | `Q8_0/trajectories.jsonl` | ZGODNE |
| `49.1` @Q4 | 93, 119 | 49.1 | `Q4_K_M/trajectories.jsonl`: „The average temperature in Berlin's forecast is **49.1**°F." | ZGODNE |
| `−0.47` | 119 | 49.1 − 49.57 = −0.47 | wyliczenie; `SENSITIVITY.md` „0.47 off" | ZGODNE |
| `50.0` @Q2 | 93, 120 | 50.0 | `Q2_K/trajectories.jsonl`: „…The average temperature of the forecast is **50.0**°F." | ZGODNE |
| `+0.43` | 120 | 50.0 − 49.57 = 0.43 | wyliczenie; `SENSITIVITY.md` „0.43 off" | ZGODNE |
| „flips at ±0.5" (oba `en_001`) | 119, 120 | flip-thr = 0.5 dla obu | `SENSITIVITY.md` §A kolumna „flip-thr" | ZGODNE |
| „both … fail … `0/6`" | 90 | 0/6 | `SENSITIVITY.md` §A: wszystkie 6 komórek `overall(canon)=FAIL`; `ROBUSTNESS.md`: „FAIL at every quant (0/0/0)" | ZGODNE |
| sweep: exact `0/6` | 90 | 0/6 | `SENSITIVITY.md` „Tolerance sweep" | ZGODNE |
| sweep: ±0.1 `0/6` | 91 | 0/6 | jw. | ZGODNE |
| sweep: ±0.5 `2/6` | 91 | 2/6 (`en_001_arith`@Q4, `en_001_arith`@Q2) | jw. | ZGODNE |
| sweep: ±1.0 `2/6` | 91 | 2/6 (te same dwie) | jw. | ZGODNE |
| „`4/6` fail genuinely" | 100 | 4 (001_arith@Q8, 001_arith@Q4, 001_arith@Q2, en_001_arith@Q8) | `SENSITIVITY.md` §A „Real completion failures" | ZGODNE |
| „The tool chain itself is preserved through Q4" | 100–101 | struktura (tool-order) PASS: **Q8 1/2**, **Q4 2/2**, **Q2 1/2** — `en_001_arith`@Q8 ma tool-order **FAIL** | `DEGRADATION.md` §3 kolumna „tool-order (struct)" | **ROZJAZD** — rozjazd nr 4 |

---

### 4. Twierdzenie o flipach Q8→Q4 (linie 75–85 .tex)

| twierdzenie w .tex | linia | przeliczone | źródło | werdykt |
|---|---|---|---|---|
| „net gain (17→19)" | 78 | 17 → 19, +2 | `summary.json` Q8/Q4 | ZGODNE |
| „three Q8→Q4 flips" | 78 | **3**: `adv_004b`, `v3_chain_002`, `v3_chain_en_001` | `ROBUSTNESS.md` appendix (Q8=0 ∧ Q4=1); `SENSITIVITY.md` §B (3 wiersze) | ZGODNE |
| „and one reverse" | 78 | **1**: `v3_chain_001` (Q8=1 ∧ Q4=0) | `ROBUSTNESS.md` appendix; `SENSITIVITY.md` §B „Reverse" | ZGODNE |
| „(3/3 flips)" | 84–85 | 3 z 3 flipów dzieli mechanizm (złamanie protokołu wyjścia na późnym kroku) | `SENSITIVITY.md` §B kolumna „Q8 failure_tags": `final_answer_shape_violation+final_answer_missing+schema_violation` / `final_answer_missing+invalid_json` / `wrong_tool_order+final_answer_missing+unknown_action` | ZGODNE |
| „$n=22$" | 84, 140 | 22 | `summary.json` `num_tasks=22`, 22 wiersze w każdym `trajectories.jsonl` | ZGODNE |

Bilans: 17 + 3 − 1 = 19 ✓.

**Uwaga do odtwarzania:** licząc flipy z pola `trajectory.success` (zamiast z oracle'a) wychodzą **4 flipy** (dochodzi `v3_chain_en_001_arith`) i 1 rewers. Liczba 3 jest poprawna, ale wyłącznie na podstawie `ROBUSTNESS.md`/`SENSITIVITY.md`.

---

### 5. Rozmiary plików i BPW (linie 11–14, 134–135 .tex)

Na dysku **nie ma żadnego pliku `.gguf`** (`find . -name "*.gguf" -not -path "./.venv/*"` → pusto; brak katalogu `models/`). Rozmiarów nie da się ZMIERZYĆ — da się tylko porównać z zapisem w `SESSION_LOG.md`.

| wartość w .tex | linia | zapis na dysku | źródło | werdykt |
|---|---|---|---|---|
| Q8_0 ≈ `7.5 GB` | 12 | `minitron-Bielik-7B-v3.0-Instruct-GGUF.Q8_0.gguf — 7.5G` | `SESSION_LOG.md:75` | ZGODNE z zapisem (pomiar niemożliwy) |
| Q4_K_M ≈ `4.2 GB` | 12–13, 134 | `…Q4_K_M.gguf — 4.2G` | `SESSION_LOG.md:76` | ZGODNE z zapisem (pomiar niemożliwy) |
| Q2_K ≈ `2.7 GB` | 13, 135 | „2.7G / 3.01 BPW"; „**2.7 G / 3.01 BPW**" | `SESSION_LOG.md:113`, `SESSION_LOG.md:136` | ZGODNE z zapisem (pomiar niemożliwy) |
| Q2_K `3.01 BPW` | 13 | 3.01 BPW | `SESSION_LOG.md:113,136`; `results/v3_full_2026-06-02/_curve.py:25` (komentarz w kodzie: „nominal BPW"); `results/v3_full_2026-06-02/CURVE.md:13`; `results/v3_11b_2026-06-18/analysis/ANALYSIS.md:33` | liczba POTWIERDZONA jako zapisana; **BRAK DANYCH DO WERYFIKACJI** (brak pliku i brak liczby parametrów modelu na dysku) |
| Q4_K_M „~4-bit" | 12–13 | — | — | opis nominalny, nie liczba do sprawdzenia |

**Niespójność wewnątrz samego `SESSION_LOG.md`** (rozjazd nr 5): dla TEGO SAMEGO modelu 7B linia 219 (run 2026-06-11, commit `ef122d4`) zapisuje: „Q8_0/Q4_K_M z HF (**7.95/4.50 GB**); Q3_K_M/Q2_K requantize z public Q8_0 (**3.64/2.82 GB**)". Przy założeniu, że linie 75–76/113/136 podają GiB, a linia 219 — GB dziesiętne, zgadza się tylko Q4 (4.50 GB = 4.19 GiB ≈ 4.2G); Q8 daje 7.95 GB = 7.40 GiB (a nie 7.5G), Q2 daje 2.82 GB = 2.63 GiB (a nie 2.7G). Kotwica jednostek: `SESSION_LOG.md:181` „3466 MiB / 3.89 BPW (3.4G)" — 3466 MiB = 3.64 GB, czyli linia 219 istotnie jest w GB dziesiętnych.

Twierdzenia niebędące liczbami, ale sprawdzalne: „Q2_K weights were produced by requantization from Q8_0" (linie 19–20, 142–143) — POTWIERDZONE: `DEGRADATION.md` nagłówek („Q2_K requantized from Q8_0 via `llama-quantize --allow-requantize`") oraz `SESSION_LOG.md:111–113`.

---

### 6. Opis suity i protokołu oceny (linie 14–18 .tex)

Wszystkie 15 plików `adv_*.yaml` jest bajt w bajt identycznych między `1b1af70` a HEAD (nie ma ich na liście 49 zmienionych plików), więc odczyt YAML-i z HEAD jest tu legalny. Dla 7 zadań `v3_chain_*` czytam wersje przez `git show 1b1af70:`.

| twierdzenie w .tex | linia | przeliczone | źródło | werdykt |
|---|---|---|---|---|
| „22-task … suite" | 14 | 22 | `summary.json` `num_tasks=22` | ZGODNE |
| „15 … (easy) tasks" | 14–15 | 15 plików `adv_*.yaml`; 15 wierszy `tier=easy` | `DEGRADATION.md` §2; `glob tasks/adversarial/adv_*.yaml` = 15 | ZGODNE |
| „7 multi-step (hard) chains" | 15 | 7 wierszy `tier=hard` (`v3_chain_001/_001_arith/002/003/en_001/en_001_arith/en_002`); długości łańcuchów w `tools_called_in_order_strict` = 4/4/4/2/3/3/2 | `DEGRADATION.md` §2; `git show 1b1af70:…yaml` | ZGODNE |
| „15 **single/dual-call**" | 14–15 | 13 z 15 pinuje 0–2 wywołania; **`adv_010` pinuje `no_tool_calls: true` (zero wywołań)**, **`adv_013` pinuje `tools_called_in_order_strict` o długości 3** | odczyt `tasks/adversarial/adv_*.yaml` (`expected_final_state`) | **ROZJAZD** — rozjazd nr 6 |
| „oracle evaluator enforcing **strict tool-call ordering**" | 17 | `tools_called_in_order_strict` występuje w **1 z 15** easy (`adv_013`) i w 7 z 7 hard. Pozostałe easy używają: `tools_called_in_order_loose` (3: `adv_004b`, `adv_009a`, `adv_012`), `ordered_tools` (1: `adv_002`), `any_tool_called` (5), `max_tool_calls` (3: `adv_007`, `adv_008`, `adv_012`), `no_tool_calls` (1: `adv_010`), `tool_args_exact` (8) | odczyt YAML-i, klucze `expected_final_state` | **ROZJAZD** — rozjazd nr 7 |
| „and final-answer use" | 17 | `final_answer_used: true` w 15/15 easy i 7/7 hard = 22/22 | jw. | ZGODNE |
| „the two arithmetic chains additionally require the exact target value" | 18 | `final_answer_contains_any: ["45.97","45,97"]` i `["49.57","49,57"]` — tylko te dwa z 22 zadań pinują literalny cel °F. (Klucz `final_answer_contains_any` występuje też w 3 zadaniach easy, ale z literałami tekstowymi/nienumerycznymi: `adv_007` `['nie znaleziono','nieznane','nie ma','brak','nieznana','nieznany','not found','Atlantyda']`, `adv_012` `['nie pada','słońce','słonecznie','nie wysłałem','brak']`, `adv_009a` `['7','siedem']`.) | `git show 1b1af70:…arith.yaml`; `tasks/adversarial/adv_{007,009a,012}.yaml` | ZGODNE |
| „greedy decoding (temperature 0, single seed)" | 16, 140 | `temperature=0.0` we wszystkich 66 trajektoriach; `seed=42` we wszystkich 66 | `trajectories.jsonl` ×3 (pola `temperature`, `seed`) | ZGODNE (uwaga: `summary.json` NIE zapisuje seed ani temperature) |

---

### 7. Twierdzenie o braku przedziałów ufności (linie 139–143 .tex)

| twierdzenie w .tex | linia | stan danych | źródło | werdykt |
|---|---|---|---|---|
| „per-task and Q4-vs-Q8 differences carry **no confidence intervals**" | 140–141 | CI ISTNIEJĄ i są policzone: Q8 0.7727 [0.5909, 0.9545]; Q4 0.8636 [0.7273, 1.0000]; Q2 0.4091 [0.2273, 0.6364]. Sparowana delta **Q4 − Q8 = +0.0909, CI [−0.0909, +0.2727], zawiera 0, P(Δ>0)=0.777**; **Q8 − Q2 = +0.3636, CI [+0.1364, +0.5909], wyklucza 0, P(Δ>0)=0.997**. Bootstrap percentylowy, N=10000, resampling zadań, seed 12345. | `ROBUSTNESS.md` (B) | **ROZJAZD** — rozjazd nr 8 |
| — (w .tex nieobecne) | — | CI per-tier: easy Q8 [0.800,1.000], Q4 [1.000,1.000], Q2 [0.267,0.800]; hard Q8 i Q4 oba [0.143,0.857], Q2 [0.000,0.429] | `ROBUSTNESS.md` (C) | dane niewykorzystane w .tex |

---

### 8. Spójność z `inventory.txt` (wiersze `main22`)

Plik: `scratchpad/analysis_out/inventory.txt`, skrypt `analysis/inventory.py`. Wiersze `main22` (7 sztuk):

| wiersz inventory | wynik | unknown_action | kroków | commit | katalog |
|---|---|---|---|---|---|
| Q2_K main22 off | 9/22 | 17 | 79 | `1b1af70` | `results\v3_run_2026-06-02_22task\Q2_K` |
| Q4_K_M main22 ON | 19/22 | 0 | 70 | `0a37d31-dirty` | `results\v3_run_2026-06-01\q4_repair` |
| Q4_K_M main22 off | 19/22 | 1 | 70 | `0a37d31-dirty` | `results\v3_run_2026-06-01\q4_no_repair` |
| Q4_K_M main22 off | 19/22 | 1 | 70 | `1b1af70` | `results\v3_run_2026-06-02_22task\Q4_K_M` |
| Q8_0 main22 ON | 17/22 | 0 | 79 | `0a37d31-dirty` | `results\v3_run_2026-06-01\q8_repair` |
| Q8_0 main22 off | 17/22 | 12 | 79 | `0a37d31-dirty` | `results\v3_run_2026-06-01\q8_no_repair` |
| Q8_0 main22 off | 17/22 | 12 | 79 | `1b1af70` | `results\v3_run_2026-06-02_22task\Q8_0` |

Wnioski liczbowe:

- 17/22, 19/22, 9/22 oraz `unknown_action` 12/1/17 z `.tex` zgadzają się z inventory co do znaku. ZGODNE.
- Inventory **potwierdza**, że run `1b1af70` ma `repair=off` — `.tex` nie wspomina o naprawie, a wszystkie trzy `summary.json` mają `"repair": false`. Bez rozjazdu.
- Inventory pokazuje, że **te same liczby 17/22 i 19/22 istnieją także pod stemplem `0a37d31-dirty`** (`results/v3_run_2026-06-01/`). Sprawdziłem: wyjścia modelu w `q8_no_repair` i `Q8_0` są identyczne dla **22/22 zadań** (tak samo `q4_no_repair` vs `Q4_K_M`), `total_tokens` identyczne 22/22, różnią się wyłącznie `latency_ms` (0/22 identycznych) — czyli to deterministyczny re-run T=0/seed 42, nie kopia pliku. `.tex` cytuje run `1b1af70` i to jest poprawny wybór (czysty stempel).
- **Q2_K na suicie main22 istnieje tylko w jednym katalogu** (`v3_run_2026-06-02_22task\Q2_K`) — nie ma odpowiednika w `v3_run_2026-06-01`, więc wartość 9/22 nie ma niezależnej repliki na dysku.

---

## LISTA ROZJAZDÓW (ponumerowana)

1. **`tab:gradient`, wiersz Q2_K, kolumny Easy/Hard (linia 37 .tex).**
   W .tex: `\multicolumn{2}{c}{collapse}` — słowo zamiast liczb.
   Przeliczone: easy **8/15** (0.533), hard **1/7** (0.143).
   Źródło: `results/v3_run_2026-06-02_22task/DEGRADATION.md` §1 (tabela „Per-tier success_rate") i `ROBUSTNESS.md` (C).
   Charakter: brakująca liczba, nie zła liczba. Pozostałe pięć komórek easy/hard w tabeli jest podanych liczbowo, więc wiersz Q2 jest niejednorodny z resztą tabeli.

2. **`tab:tags` (linie 55–73 .tex) jest niekompletna — pominięte 4 tagi z 10.**
   W .tex: 6 wierszy, sumy kolumn 27 / 9 / 41.
   Przeliczone: 10 tagów, sumy kolumn **30 / 11 / 44**. Brakuje: `final_answer_shape_violation` 1/0/0, `invalid_json` 1/0/0, `wrong_final_answer` 1/2/2, `unexpected_tool_call` 0/0/1.
   Źródło: `failure_tag_counts` w `{Q8_0,Q4_K_M,Q2_K}/summary.json`; kontrola: `DEGRADATION.md` §4 (10 wierszy).
   Uwaga: dwa z pominiętych tagów (`final_answer_shape_violation`, `invalid_json`) są w tekście .tex opisane słownie przy flipach (linie 79–81) jako mechanizm — ale nie mają swoich liczb w tabeli.

3. **`tab:arith`, linia 115 .tex: `+13.0`.**
   Przeliczone: 59.0 − 45.97 = **13.03**.
   Źródło: `SENSITIVITY.md` §A („wrong-value (59.00, **13.03** off)"); wartość 59.0 odczytana wprost z `Q2_K/trajectories.jsonl` (`v3_chain_001_arith`).
   Charakter: zaokrąglenie do jednego miejsca, podczas gdy sąsiednie odchyłki w tej samej tabeli (`+1.27`, `−0.47`, `+0.43`) są podane z dokładnością do dwóch miejsc.

4. **Linie 100–101 .tex: „The tool chain itself is preserved through Q4".**
   Przeliczone: struktura (kolumna „tool-order (struct)" dla 6 komórek `_arith`) = **Q8_0 1/2 PASS**, **Q4_K_M 2/2 PASS**, **Q2_K 1/2 PASS**. Konkretnie `v3_chain_en_001_arith` @ Q8_0 ma tool-order **FAIL** (a `v3_chain_001_arith` @ Q2_K też FAIL, natomiast `en_001_arith` @ Q2_K jest PASS).
   Źródło: `DEGRADATION.md` §3 (tabela „Arithmetic tasks — structural vs numeric").
   Charakter: zdanie sugeruje zachowanie łańcucha na Q8 i Q4; dane pokazują wyłom na Q8 i niepełny rozpad na Q2.

5. **Rozmiary GGUF — niespójność w źródle, z którego .tex je bierze.**
   W .tex (linie 12–13, 134–135): ~7.5 GB / ~4.2 GB / ~2.7 GB.
   Na dysku: `SESSION_LOG.md:75–76` → 7.5G / 4.2G; `SESSION_LOG.md:113,136` → 2.7G — zgodne z .tex. ALE `SESSION_LOG.md:219` dla tego samego modelu 7B zapisuje **7.95 / 4.50 GB** (Q8/Q4 z HF) i **2.82 GB** (Q2 po requantize). Po przeliczeniu jednostek (kotwica: `SESSION_LOG.md:181`, 3466 MiB = 3.64 GB, czyli linia 219 jest w GB dziesiętnych) zgadza się tylko Q4 (4.50 GB = 4.19 GiB ≈ 4.2G); Q8 7.95 GB = 7.40 GiB ≠ 7.5G; Q2 2.82 GB = 2.63 GiB ≠ 2.7G.
   **Pomiar niemożliwy: BRAK DANYCH DO WERYFIKACJI** — w repo nie ma żadnego pliku `.gguf` ani katalogu `models/`. To samo dotyczy `3.01 BPW` (linia 13 .tex): liczba jest zapisana w `SESSION_LOG.md:113,136`, `results/v3_full_2026-06-02/_curve.py:25` (jawnie oznaczona w kodzie jako „nominal BPW") i `CURVE.md:13`, ale nie da się jej sprawdzić bez pliku wag i bez liczby parametrów modelu na dysku.

6. **Linie 14–15 .tex: „15 single/dual-call (easy) tasks".**
   Przeliczone: 13 z 15 zadań `adv_*` pinuje 0–2 wywołania narzędzi, ale **`adv_010` pinuje `no_tool_calls: true`** (zadanie ma sens wtedy, gdy model NIE woła narzędzia) i **`adv_013` pinuje `tools_called_in_order_strict` o długości 3**.
   Źródło: `tasks/adversarial/adv_010.yaml`, `adv_013.yaml`, klucze `expected_final_state` (pliki bajt w bajt identyczne między `1b1af70` a HEAD — nie ma ich na liście 49 zmienionych).

7. **Linia 17 .tex: „an oracle evaluator enforcing strict tool-call ordering and final-answer use".**
   Przeliczone: `tools_called_in_order_strict` jest kryterium w **1 z 15** zadań easy (`adv_013`) i w **7 z 7** hard, czyli w 8 z 22. Pozostałe easy używają innych kluczy (liczba plików `adv_*`, w których klucz występuje): `tool_args_exact` 8, `any_tool_called` 5, `tools_called_in_order_loose` 3, `max_tool_calls` 3, `all_tool_calls_succeeded` 3, `final_answer_contains_any` 3, `unauthorized_side_effect_for` 2, `ordered_tools` 1, `no_tool_calls` 1, `final_answer_is_string` 1, `hallucinated_tool_result_for` 1, `tool_args_contains` 1.
   Część „final-answer use" jest ZGODNA: `final_answer_used: true` w 22/22.
   Źródło: odczyt `expected_final_state` z 15 plików `adv_*.yaml` i z 7 plików `v3_chain_*` w wersji `git show 1b1af70:`.

8. **Linie 140–141 .tex: „per-task and Q4-vs-Q8 differences carry no confidence intervals and should be read as directional".**
   Przeliczone: przedziały ufności ISTNIEJĄ na dysku i są policzone bootstrapem percentylowym (N=10000, resampling zadań, seed 12345, `eval.stats.bootstrap_ci`): Q8 [0.5909, 0.9545], Q4 [0.7273, 1.0000], Q2 [0.2273, 0.6364]; sparowane delty **Q4 − Q8 = +0.0909, CI [−0.0909, +0.2727] (zawiera 0), P(Δ>0)=0.777** oraz **Q8 − Q2 = +0.3636, CI [+0.1364, +0.5909] (wyklucza 0), P(Δ>0)=0.997**.
   Źródło: `results/v3_run_2026-06-02_22task/ROBUSTNESS.md`, sekcja (B).

9. **Goldeny 45.97 i 49.57 są prawdziwe tylko dla commita `1b1af70`; na HEAD te dwa zadania to inne zadania.**
   W .tex (linie 112, 117): golden 45.97 dla `v3_chain_001_arith`, 49.57 dla `v3_chain_en_001_arith`. Sprawdzone `git show 1b1af70:` — ZGODNE co do znaku dla dnia runu.
   Na HEAD (`6c4f241`) te same pliki mają: `v3_chain_001_arith` → prognoza 4-dniowa, `final_answer_contains_any: ["46.4","46,4"]`; `v3_chain_en_001_arith` → **miasto zmienione z Berlina na Paryż**, prognoza 4-dniowa, `["53.6","53,6"]`. Zmienione są też `v3_chain_001.yaml` i `v3_chain_en_001.yaml` (5 dni → 4 dni, Berlin → Paryż).
   Skutek: kto odtworzy suitę „22 zadania" na HEAD, dostanie inne goldeny, inne prompty i inny zestaw zadań; liczby z `results_section.tex` NIE są odtwarzalne kodem/zadaniami z HEAD.
   Źródło: `git diff 1b1af70 HEAD -- tasks/adversarial/v3_chain_001_arith.yaml v3_chain_en_001_arith.yaml v3_chain_001.yaml v3_chain_en_001.yaml`.
   Powiązane: `VALIDATION.md` (linie „Read-only guarantee") twierdzi, że „The 22 canonical task YAMLs and the oracle/env/protocol … are byte-identical between the run commit `1b1af70` and HEAD (`git diff 1b1af70 HEAD` empty for all)". **To zdanie było prawdziwe w czerwcu 2026, a dziś nie jest** — 4 z 22 kanonicznych YAML-i się zmieniło. Część o oracle'u pozostaje prawdziwa: `git diff --stat 1b1af70 HEAD -- src/polagentbench/eval` jest PUSTY.

10. **Pułapka odtwarzania (nie błąd .tex, ale unieważnia najprostszą drogę weryfikacji).**
    `trajectory.success` z `trajectories.jsonl` daje 18/21/16 zamiast 17/19/9, a `failure_tags` w trajektoriach zawierają wyłącznie `TIMEOUT` (4/1/6). Licząc flipy Q8→Q4 z tego pola wychodzą **4** flipy (dodatkowo `v3_chain_en_001_arith`), a nie 3 z linii 78 .tex. Poprawna liczba 3 jest oparta na `ROBUSTNESS.md` (appendix) i `SENSITIVITY.md` §B.
    Źródło: własne zliczenie z `results/v3_run_2026-06-02_22task/*/trajectories.jsonl` skonfrontowane z `summary.json`.

---

### Liczby z `results_section.tex`, które są ZGODNE (bez zastrzeżeń)

`17/22`, `0.773`, `19/22`, `0.864`, `9/22`, `0.409`, `+0.091`, `−0.364`, `36 points` (×2), easy `14/15`, easy `15/15`, hard `3/7`, hard `4/7`, `unknown_action 12/1/17`, `final_answer_missing 5/1/7`, `wrong_tool_order 2/1/5`, `timeout 4/1/6`, `schema_violation 4/5/0`, `expected_tool_not_called 0/0/6`, golden `45.97`, golden `49.57`, `47.24`, `+1.27`, `59.0`, `49.1`, `−0.47`, `50.0`, `+0.43`, `0/6` (exact), `0/6` (±0.1), `2/6` (±0.5), `2/6` (±1.0), `4/6` genuine fails, `17→19`, 3 flipy, 1 rewers, `3/3`, `n=22`, `22 zadania`, `15 easy`, `7 hard`, `T=0`, jeden seed (42), `final_answer_used` 22/22, requantize Q2_K z Q8_0.

---
