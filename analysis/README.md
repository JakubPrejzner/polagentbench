# analysis/ — skrypty odtwarzające tabele do papera

Skrypty diagnostyczne, każdy **wyłącznie do odczytu**: czytają `results/**/run.log`,
`results/**/trajectories.jsonl`, `results/**/summary.json` i `tasks/**/*.yaml`, nic nie zapisują
i nic nie modyfikują. Żaden nie potrzebuje GPU ani sieci — wszystkie liczby powstają z danych,
które już leżą na dysku.

## Uruchamianie

```
cd <katalog główny repo>
.venv/Scripts/python.exe analysis/<skrypt>.py
```

Ścieżki w skryptach są **względne wobec katalogu głównego repo** — uruchomienie z wnętrza
`analysis/` nie zadziała. Część skryptów importuje kod repo (`sys.path.insert(0, "src")`),
co również zakłada uruchomienie z góry. Wymagany interpreter to `.venv/Scripts/python.exe`;
systemowy Python nie ma `pydantic` ani `pyyaml`.

Skrypty `bootstrap_ci.py` i `ladder_typing_tolerant.py` korzystają z `release_paths.py`, więc
z czystego klona czytają dane z `release_data/`. Uruchom je z katalogu głównego repo poleceniami
`.venv/Scripts/python.exe -B analysis/bootstrap_ci.py` oraz
`.venv/Scripts/python.exe -B analysis/ladder_typing_tolerant.py`.

**Uwaga o danych:** `results/` jest w `.gitignore` (linia 55), więc surowe dane **nie są
w tym repo**. Bez nich skrypty nie mają czego czytać. Kopia danych żyje osobno — patrz
release `backup-20260821`.

## Mapa: skrypt → tabela / finding

### Inwentarz

| skrypt | produkuje | kluczowa liczba |
|---|---|---|
| `inventory.py` | tabela inwentarza 120 runów | jedyny run `main67` z 18 spłaszczonymi kopertami to PLLuM-8B Q8, nie Bielik-7B (te mają 31 i 50) |

Ten skrypt służy do **targetowania** — puszczać go przed każdą nową analizą, żeby nie liczyć
na niewłaściwym runie.

### PLLuM: zepsuty szablon czy brak zdolności

| skrypt | produkuje | kluczowa liczba |
|---|---|---|
| `pllum_raw_dump.py` | Analiza 1, sekcja 1b (cytaty) | poprawne koperty `call_tool` obok spłaszczonych; `adv_010` = rozmowa modelu z samym sobą |
| `pllum_patterns.py` | Analiza 1, TABELA 1a (kolumna PLLuM) | 83,9% kroków parsuje się poprawnie; **0 artefaktów szablonu** |
| `pllum_vs_bielik.py` | Analiza 1, TABELA 1a i TABELA 1c | rozkład tagów odwrócony: PLLuM 74 TREŚĆ / 29 FORMAT, Bielik 15 / 43 |
| `pllum_ceiling.py` | Analiza 1, TABELA 1d | **sufit hojny 32/67 = 0.478** < faktyczne 0.806 Bielika; 35 z 54 porażek bez błędu formatu |

**Finding:** to nie jest zepsuty szablon. Nawet przy darowaniu każdej porażki dotkniętej błędem
składni PLLuM nie dociąga do Bielika.

### Wariancja seedów: dwumodalność przy T=0.7

| skrypt | produkuje | kluczowa liczba |
|---|---|---|
| `variance_seed_config.py` | Analiza 2, TABELA 2a i 2b | seed jest w rekordach trajektorii (1/2/3, T=0.7), choć w `summary.json` jest `None`; seed1 wyprodukował **więcej** tekstu i pracował **dłużej** niż seed2 |
| `variance_classify.py` | Analiza 2, TABELA 2c | seed1 po darowaniu kaskad: **0.776 (Q8)** i **0.881 (Q3)** — pasmo seedów 2 i 3 |
| `variance_repetition.py` | Analiza 2, TABELA 2d + cytaty 2c | hipoteza „zaklinowany sampler" **obalona**: najwięcej powtórzeń ma seed3 (13,7%), który punktuje najlepiej |

**Finding:** zapaść seed=1 to utrata dyscypliny koperty, nie utrata zdolności — treść odpowiedzi
bywa identyczna z tą, którą seed2 zalicza.

### Drabina: rozbicie na szczeble

| skrypt | produkuje | kluczowa liczba |
|---|---|---|
| `ladder_rungs.py` | Analiza 3, opis szczebli | L0 **zabrania** wywołań narzędzi; L3N wymaga **dwóch** konwersji |
| `ladder_breakdown.py` | Analiza 3, TABELA 1 i TABELA 2 | **SKRÓT = 0 w 80 zadaniach L3N** → rata tolerancyjna = ścisła |
| `ladder_pllum_rungs.py` | `paper/tables/ladder.tex`, sześć wierszy PLLuM | całe **2 zaliczenia PLLuM na drabinie**: Q8_0 na L0 (`v3_ext_L0_c`, `v3_ext_L0_f`), pięć niższych kwantów **0/46** |
| `ladder_nearmiss.py` | Analiza 3, blok „Dlaczego SKRÓT jest pusty" | poprawny łańcuch + poprawny golden, odrzucone na **typie** pola `answer` (float w 11B, dict w 7B) |
| `ladder_typing_tolerant.py` | Analiza 3, TABELA 3 | L3N na 11B Q8: **0.20 → 0.90**; na 7B Q8: 0.00 → 0.70 |
| `ladder_controls.py` | Analiza 3, kontrola + przyczyny L0 | L1/L2 **nie** darowane, bo golden nieobecny (59 zamiast 46.4); L0 = 0.00 ma dwie różne przyczyny |

**Finding:** przewidywany SKRÓT nie istnieje. Bliskie porażki L3N to wyłącznie typowanie pola
`answer`. `ladder_controls.py` jest kontrolą, że tolerancja nie rozdaje darmowych punktów.

### Dip Q4 na Bielik-11B

| skrypt | produkuje | kluczowa liczba |
|---|---|---|
| `q4dip_classify.py` | Analiza 1, TABELA 1a i 1b | dip kurczy się z **−0.209 do −0.090** wobec Q5, ale **nie znika** |
| `q4dip_depth.py` | Analiza 1, TABELA 1c i 1e | cały dip w kubełku **4+ wywołań** (0.32 vs 0.84); przy 2–3 Q4 jest **wyżej** niż Q5 |
| `q4dip_deep_ceiling.py` | Analiza 1, TABELA 1d | w kubełku 4+ po darowaniu A+B dip nadal **−0.320**; Q5 osiąga 25/25 |
| `q4dip_group.py` | Analiza 1, TABELA 1f | 14 zadań padających tylko na Q4 to **spójna grupa**: 79% ma ≥4 wywołania przy 37% w suicie; 6 z 14 ma identyczny zestaw tagów |

**Finding:** dip Q4 to degradacja dyscypliny koperty ujawniająca się dopiero powyżej trzech
wywołań narzędzi, gdzie zamienia się w niedokończone łańcuchy i timeouty.

### Atraktor „59"

| skrypt | produkuje | kluczowa liczba |
|---|---|---|
| `attractor59_cases.py` | Analiza 2, TABELA 2a | 4 zadania L1, 3 różne goldeny, **ta sama odpowiedź 59** |
| `attractor59_count.py` | Analiza 2, TABELA 2b i 2c | 59.0 to **najczęstsza liczbowa odpowiedź w zbiorze**: 91 par, 26 zadań, 23 runy, oba modele |
| `attractor59_negative_controls.py` | Analiza 2, TABELA 2d w. 1–5 | 59 nie jest goldenem **żadnego** zadania; nie ma go w `weather.py`; 15 °C nie istnieje w środowisku |
| `attractor59_direction.py` | Analiza 2, TABELA 2d w. 6 | wszystkie 11 przypadków z 59 w wyniku narzędzia: model sam podał `value=15` |
| `attractor59_scan_raw.py` | *materiał pomocniczy* | **NIE używać do liczb** — zlicza obiekty JSON, zawyża (61 → 4189 zamiast 32) |

**Finding:** 59 = F(15 °C) to atraktor spoza kontekstu — fallback na pamięć parametryczną przy
poprawnie wykonanym łańcuchu narzędzi.

### Envelope collapse: rozdzielenie zmiennych

| skrypt | produkuje | kluczowa liczba |
|---|---|---|
| `envelope_positions.py` | Analiza 3, TABELA 3a, 3b, 3c | (b) i (c) **niepuste** → pozycja i narzędzie **nie są skonfundowane** |
| `envelope_marginals.py` | Analiza 3, TABELA 3d | iloraz ryzyka: narzędzie **3.95×**, pozycja **0.60×** → dominuje narzędzie |

**Finding:** spłaszczanie koperty u PLLuM jest efektem specyficznym dla `convert_temperature`,
nie efektem głębokości łańcucha. U Bielika-7B żadna z dwóch zmiennych nie tłumaczy niczego.

### Tryby porażki i koszt trajektorii

| skrypt | produkuje | kluczowa liczba |
|---|---|---|
| `mode_tables.py` | cztery tabele naraz: `tab:purity`, `tab:modes`, `tab:tokens`, `tab:tokens-full` — 18 komórek `main67` (repair=off) | artefakt zaokrągleniowy pada **dokładnie raz w całej siatce**, na 7B `Q5_K_M`; komórka 7B `Q6_K` ma **0 z 21 porażek jednokategoryjnych**, czyli jest najmniej rozstrzygniętą etykietą w Tab. 1 |

Jedyny skrypt w tym katalogu, który czyta **`release_data/`, nie `results/`** — działa więc
z samego klona repo, bez surowych katalogów runów. Werdykty wyłącznie z oracle'a
(`eval.smoke.evaluate`), etykiety z `failure_classifier.py`. Ma wbudowaną bramkę: 36 komórek
opublikowanych w paperze jest wpisanych ręcznie w `PUBLISHED_MODES` / `PUBLISHED_TOKENS`,
skrypt porównuje się z nimi i kończy kodem 1 przy jakimkolwiek rozjeździe. Komórki 7B `Q6_K`
i `Q5_K_M` (oznaczone `NOWA`) zostały dopisane do papera tym skryptem, po tym jak przeszedł
bramkę na wszystkich pozostałych.

Pułapka wyboru runów: w `runs.csv` sześć runów `v3_11b_variance_*` ma ten sam `model_id`,
`quant`, `suite` i `repair` co komórki 11B `Q8_0` i `Q3_K_M`, a jest to sonda wariancji przy
`T=0.7` (Tab. 9), nie krzywa główna. Skrypt je wyklucza, wymaga dokładnie jednego runu na
komórkę i sprawdza, że każda czytana trajektoria ma `temperature == 0`.

### Podłoga szumu: bootstrap CI

| skrypt | produkuje | kluczowa liczba |
|---|---|---|
| `bootstrap_ci.py` | tabela CI 95% dla 18 komórek `main67` (repair=off) + druga tabela dla repair=ON + blok porównań (a) Q8/Q6/Q5 i (b) Q3→Q2 | przedziały Q8, Q6 i Q5 **nachodzą na siebie u wszystkich trzech modeli** (część wspólna całej trójki: 11B `[0.746, 0.851]`, 7B `[0.403, 0.567]`, PLLuM `[0.104, 0.179]`), a spadek Q3→Q2 przekracza szerszy z dwóch CI o **44,8 pp** (11B), **7,5 pp** (7B) i **1,5 pp** (PLLuM) |

Bootstrap percentylowy, przedział 95%, **resampling po zadaniach** (wektor 0/1 długości 67,
losowanie ze zwracaniem), 10 000 prób. Ziarno na sztywno `SEED = 42` (to samo, przy którym policzono przedziały w paperze), wektor uporządkowany
rosnąco po `task_id`, `random.Random(SEED)` tworzony osobno dla każdej komórki — wynik jest
odtwarzalny co do cyfry (sprawdzone trzema przebiegami, identyczne bajt w bajt). Werdykty
wyłącznie z oracle'a: `run.log` tam, gdzie istnieje (7B Q5/Q6 i wszystkie komórki PLLuM),
odtworzenie przez `eval.smoke.evaluate` tam, gdzie go nie ma (11B Q2–Q8, 7B Q2/Q3/Q4/Q8).
Każda komórka przechodzi walidację `len(wektor) == 67` **i** `sum(wektor) == summary.num_passed`;
przy uruchomieniu z 2026-08-23 **0 rozjazdów na 36 komórek** (18 repair=off + 18 repair=ON).

**Finding:** różnice między Q8, Q6 i Q5 mieszczą się w szumie próby — na tej suicie nie da się
ich rozstrzygnąć. Q3→Q2 jest jedynym spadkiem, który wychodzi poza szerokość CI u wszystkich
trzech modeli, ale margines jest ostry tylko na 11B (3,00× szerokości CI); na PLLuM wynosi
1,08× szerokości CI, czyli ledwie.

## Dwie rzeczy, o których trzeba wiedzieć czytając wyniki

**1. Dwa katalogi nie mają `run.log`.** `results/v3_11b_2026-06-18/` (commit `a023c3b`) i
`results/v3_full_2026-06-02/` przechowują tylko `summary.json` + `trajectories.jsonl`.
Skrypty z rodziny `q4dip_*` odtwarzają więc werdykty oracle kodem repo
(`polagentbench.eval.smoke.evaluate`). Odtworzenie jest walidowane w dwie strony — wobec
`num_passed` z `summary.json` **i** wobec `analysis/per_task_matrix.csv` — i wymaga zera
rozjazdów. Warunek, który to legalizuje: `tasks/adversarial/` oraz `src/polagentbench/eval/`
są bajt w bajt identyczne między `a023c3b` a HEAD (`git diff --stat a023c3b HEAD -- <ścieżka>`
jest puste). **Przed ponownym użyciem tych skryptów na innym commicie sprawdź ten diff.**

**2. Flaga `trajectory.success` nie jest oracle'em.** W runie PLLuM Q8 flaga daje 66/67, a oracle
13/67. Wszystkie liczby w tabelach pochodzą z oracle'a (`run.log` albo `evaluate()`), nigdy
z `trajectory.success`. Podobnie `summary.json` **nie zapisuje** `seed` ani `temperature` na
najwyższym poziomie (oba `None`) — te pola są w rekordach trajektorii i stamtąd je czytamy.
