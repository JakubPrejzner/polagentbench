# PolAgentBench Session Log

Format: append-only chronological log. Każdy znaczący krok = jeden wpis.
Decision trail dla paper methods section. Wyniki runów żyją w `results/`, nie tutaj.

---

## Session 04 — 2026-05-15

### Goal
Q8 baseline integrity check → decide rerun vs reuse → proceed to Q4_K_M gradient test (Phase 1).

### Phase 0: Diagnostic

#### Step: Vast results inventory
- Vast HEAD: N/A (`/workspace/polagentbench/` does not exist after restart — empty disk)
- Local HEAD: `310ad1f` (test(suite): cover new oracles + adapt CLI/load tests for 13-task suite)
- Match: no (Vast has no repo at all)
- Q8 results present: yes — locally only: `results/adv_run_003_v2_no_repair/`, `results/adv_run_004_v2_repair/` (bielik-minitron-7b-v3 / Q8_0, temps [0.0, 0.3, 0.7], seeds [42, 43, 44], 15 task slots = adv_001..adv_013 with adv_004 and adv_009 splits)
- Meta.json commit stamp: no — pipeline does not produce `meta.json` at all; `summary.json` lacks `commit_hash` / `git_ref` field. **TODO Phase 1: add commit stamping to pipeline output.**
- Recommendation: **RERUN**

#### Reasoning
Vast post-restart is bare metal — `/workspace/polagentbench` brak, więc Faza 1 i tak wymaga full rebuild (clone repo, venv, build llama-cpp-python, fetch GGUF). Lokalne Q8 runy z 2026-05-07 są technicznie kompletne (135 trajektorii × 2 repair conditions), ale bez commit-hash stamp w summary.json nie da się zweryfikować, że pochodzą z obecnego HEAD `310ad1f` lub jego przodka — ostatni commit po dacie runów (`310ad1f`) zmienia tylko testy, więc *prawdopodobnie* są kompatybilne, ale dla paper methods section "prawdopodobnie" jest niewystarczające. Koszt re-runu Q8 to ~10 min na świeżym Vaście (po setup'ie w Fazie 1), zysk: deterministyczne, stemplowane wyniki które będą paired comparison anchor dla Q4_K_M gradient test.

#### Side observation
W root repo `C:\Users\japre\polagentbench` jest ~13 untracked plików ze zmasakrowanymi nazwami (fragmenty promptu z Session 03.5 zapisane jako file names — np. `huj`, `tatus`, `"trict\357\200\272"`, etc.). Nie usuwam — user powinien zdecydować `git clean -n` vs manual review. Nie blokują Fazy 1.

#### TODO Phase 1
- [ ] Add `commit_hash` field to `summary.json` (in `cli/run_suite.py` lub gdzieś w runner) — z `git rev-parse HEAD`
- [ ] Rebuild Vast environment: clone repo, setup .venv, install llama-cpp-python with CUDA, fetch GGUF for Q8_0 + Q4_K_M
- [ ] Re-run Q8_0 baseline (repair=on + off) na świeżym Vaście, z commit-stamped output
- [ ] Run Q4_K_M na tym samym suite/temps/seeds
- [ ] Paired McNemar Q8 vs Q4_K_M per task

### Phase 1a: Cleanup

#### Step: remove session 03.5 prompt-echo artifacts
Wszystkie pliki untracked z timestampem 2026-05-15 17:28 to fragmenty promptu zapisane jako nazwy plików (echo bufferu z poprzedniej sesji). Usunięto 10 sztuk:

1. `eline integrity check → decide rerun vs reuse → proceed to Q4_K_M gradient test (Phase 1).` (941 B)
2. `h z Vasta vs lokalny HEAD. Sprawdź czy meta.json z Q8 runów (jeśli istnieją) ma commit hash stemplowany - pipeline powinien to robić, jeśli nie, to też informacja.` (3684 B)
3. `huj` (16465 B)
4. `ion trail dla paper methods section. Wyniki runów żyją w , nie tutaj.` (16465 B)
5. `sword prompt (klucze są setup'owane przez Vast UI)` (16465 B)
6. `t HEAD: <commit hash>` (941 B)
7. `t po restartcie: repo i .venv mogą wymagać rebuild w Fazie 1, ale dziś nas to nie obchodzi` (16465 B)
8. `ta zebrane (ls results, find meta, git log, git status, models)` (9257 B)
9. `tatus` (941 B)
10. `trict:` (941 B)

Zachowane untracked (legit): `.claude/`, `SESSION_LOG.md`, `docs/prompt_03_5_report.md`.

Commit: `0c05694` (`chore: remove session 03.5 prompt-echo artifacts from root`, empty commit, audit-trail only — usuwane pliki były untracked).

### Phase 1a: Setup completed

#### Step: pipeline patch — commit stamping
Dodano `cli._git_info()` (subprocess: `git rev-parse HEAD` + `git describe --always --dirty`, 5s timeout, fallback `"unknown"` przy `FileNotFoundError`/`SubprocessError`). Wstrzyknięte do summary.json zarówno w `_run_suite` (single-temp) jak i `_run_grid` (grid). Dodane 4 testy w `tests/test_cli.py` (real-repo, mocked-failure, `run` write-out, grid `run-suite` write-out). Lokalnie 204/204 pass.

Commit: `0a37d31` (`feat(eval): stamp summary.json with commit_hash and git_ref`, 2 files / 108 insertions).

#### Step: Vast rebuild
- Tar-pipe sync z lokalnego repo (excludes: `.venv`, `results`, `models`, `*.gguf`, `.claude`, caches) → `/workspace/polagentbench`
- `git config --global --add safe.directory /workspace/polagentbench` (post-extract ownership fix)
- Vast HEAD: `0a37d31` (matches local)
- `uv sync --extra dev`: created `.venv` (CPython 3.11.15), 15 packages installed
- `CMAKE_ARGS="-DGGML_CUDA=on" uv pip install llama-cpp-python --force-reinstall --no-cache-dir`: built llama-cpp-python `0.3.23` in 6m 46s on RTX 4090 + CUDA 13.0 (nvcc V13.0.88)
- Import smoke: `from llama_cpp import Llama` OK
- `uv run pytest -q` on Vast: 204/204 pass in 3.52s
- `uv pip install huggingface_hub[cli]`: installed `huggingface-hub==1.15.0` + deps. Note: CLI command is `hf` (not `huggingface-cli download` — `huggingface-cli` exists but routes to `hf` v1; download subcommand syntax changed).

#### Step: GGUF download
HF repo `speakleash/Bielik-Minitron-7B-v3.0-Instruct-GGUF` (prefix flipped vs. expected — actual filenames are `minitron-Bielik-…`, not `Bielik-Minitron-…`):
- `minitron-Bielik-7B-v3.0-Instruct-GGUF.Q8_0.gguf` — 7.5G ✓
- `minitron-Bielik-7B-v3.0-Instruct-GGUF.Q4_K_M.gguf` — 4.2G ✓

#### Step: determinism check
Task: `tasks/smoke/weather_smoke_001.yaml` (single-tool Polish weather query, krótki).
Parameters: Q8_0 / temperature=0.0 / seed=42 / repair=off / max-tokens default. Two consecutive runs to `/tmp/det1`, `/tmp/det2`.

- `sha256(trajectories.jsonl)`: DIFFERS (`f9febaeb…` vs `ae764446…`) — latency_ms float timestamps embedded per step are the only known source.
- Semantic diff over `(parsed_action, raw_model_output, parse_error, tool_result.ok)` for each step: **BIT-IDENTICAL**. Both runs: `get_weather(city='Kraków') -> final_answer`, raw model token strings identical.

**Verdict: greedy llama.cpp on CUDA 13 / 4090 is fully deterministic at T=0 across (model_load + run) cycles. Latency wobble is the only non-deterministic signal and it does not enter eval.**

**Decision: 1 seed (42) is sufficient for Phase 1b T=0 paired Q8 vs Q4_K_M baseline.** If we later expand to T>0 ablation we will need 3+ seeds for variance estimates, but T=0 baseline is single-seed.

#### Next
- Wait for user approval → Phase 1b (Q8_0 baseline, T=0, seed=42, repair both on+off, 13-task suite → `results/q8_baseline_2026-05-15/`)
- Phase 1c (Q4_K_M, same params) → paired McNemar Q8 vs Q4_K_M per task

## 2026-06-01 — v3 hard tier + Q8/Q4/Q2 gradient

### Suite v3 — hard tier (7 data-dependency chains)
7 łańcuchów w tasks/adversarial/v3_chain_*.yaml, wszystkie zwalidowane offline (PASS na złotej
trajektorii). Osie: długość łańcucha (2-4 tool), język (PL_EN / EN_EN — EN_EN bez find_nearest_city
bo graf _NEIGHBOURS tylko PL), ocena (struktura / struktura+arytmetyka). Pułapka kolejności:
find_nearest_city zwraca w kolejności grafu nie po dystansie (Warszawa→pierwszy Łódź 130km mimo
Radom 100km). Listy arith zawężone do dokładnej wartości + oba separatory: 45.97/45,97 (chain_001),
49.57/49,57 (en_001). Easy tier = 15 adv_* z poprzedniego suite.

### Run 2026-06-01 (commit 0a37d31, llama-cpp 0.3.19 cu124 wheel, RTX 4090, T=0 seed=42)
Pełne pass_rate per (model × repair × tier):
- Q8_0  off: easy 0.9333 (14/15), hard 0.4286 (3/7)
- Q8_0  on : easy 0.9333,         hard 0.4286
- Q4_K_M off: easy 1.0000 (15/15), hard 0.5714 (4/7)
- Q4_K_M on : easy 1.0000,         hard 0.5714
Wyniki lokalnie: results/v3_run_2026-06-01/{q8,q4}_{no_repair,repair}/ + _sanity_easy_q8/.

### Q2_K (requantize z Q8_0)
F16/safetensors gated (brak public F16) → requantize z public Q8_0 (llama-quantize --allow-requantize,
CPU-build llama.cpp by ominąć CUDA-13). 2.7G / 3.01 BPW. Koherencja OK (poprawna polszczyzna).
Recipe w pamięci project_polagentbench.md.
- Q2 sanity easy = 0.5333 (8/15) — zdegradowany ale wciąż agentowy (>0.5). Faile: unknown_action ×8,
  pętle, brak final_answer. Mechanizm INNY niż Q8 (Q8 = over-thinking/pętle do max_steps).
- Q2 FULL gradient (22 taski) — UTRACONY: box destroyed zanim scp. DO POWTÓRZENIA.

### Kluczowe findingi
1. Hard tier zbił sufit (easy 0.93-1.0 → hard 0.43-0.57) — trudność agentowa różnicuje tam gdzie
   single-call nie potrafił.
2. AQG Q8→Q4 UJEMNY (Q4 lepszy) drugi raz z rzędu. Mechanizm: Q8 over-thinkuje, wpada w pętle,
   wyczerpuje max_steps (12471 tok fail); Q4 zwięźlejszy, kończy (8206 tok pass). Przeciwne do H1.
3. Arytmetyka łamie OBA (Q8 i Q4) — failure w rozumowaniu na danych, nie w orkiestracji.
4. n=7 hard → BRAK mocy statystycznej (różnice 1 task, McNemar p≈1.0). Findingi jakościowe, nie ilościowe.

### NASTĘPNY KROK
Rozbudowa hard tier 7→~25 łańcuchów (offline) → jeden duży run Q8/Q4/Q2 × rozbudowany suite.
Q2 full odtworzyć z recipe (requantize z Q8_0, ~3 min) jako część tego runu, nie osobno.

## 2026-06-02 — full gradient 45 tasks Q8/Q4/Q2 (HEAD d6088b3)

Box: Vast RTX 4090 (24 GB), CUDA 13.1, instance 39177922 ($0.69/hr). llama-cpp-python **0.3.19**
(abetlen cu124 prebuilt wheel + nvidia-cuda-runtime-cu12/cublas-cu12 + LD_LIBRARY_PATH; NIE source-build —
CUDA-13 nvcc dalej pada). Q2_K = requantize z public Q8_0 (CPU-build `llama-quantize --allow-requantize`,
**2.7 G / 3.01 BPW**, koherentny PL). Suite = pełne **45 tasków** (15 easy adv_* + 30 hard v3_chain_*),
T=0 / seed 42 / max-tokens default. pytest 204/204. Sanity gate easy-Q8 = 0.9333 (reprodukcja poprzedniego runu).
Wszystkie 6 summary.json stamped **commit_hash=d6088b3 (CZYSTY)**, git_ref=d6088b3. Oracle re-eval `evaluate()`
== summary.num_passed dla wszystkich 6. Stare wyniki 0a37d31-dirty/22-task NIE mieszane.
Wyniki: `results/v3_full_2026-06-02/{q8,q4,q2}_{no_repair,repair}/` + `per_task_table.csv` (270 wierszy).

### Agregat pass_rate (model × repair × tier)
| model  | repair | easy (15)   | hard (30)   | all (45)    | avg_tok(all) |
|--------|--------|-------------|-------------|-------------|--------------|
| Q8_0   | off    | 0.9333 (14) | 0.3333 (10) | 0.5333 (24) | 7570  |
| Q8_0   | on     | 0.9333 (14) | 0.4333 (13) | 0.6000 (27) | 7304  |
| Q4_K_M | off    | 1.0000 (15) | 0.4333 (13) | 0.6222 (28) | 7666  |
| Q4_K_M | on     | 1.0000 (15) | 0.4333 (13) | 0.6222 (28) | 7684  |
| Q2_K   | off    | 0.5333 (8)  | 0.1667 (5)  | 0.2889 (13) | 13690 |
| Q2_K   | on     | 0.6667 (10) | 0.1667 (5)  | 0.3333 (15) | 13613 |

### McNemar exact (two-sided), repair=off, paired per tier (b=first-only pass, c=second-only pass)
| para        | easy (15)        | hard (30)        | all (45)          |
|-------------|------------------|------------------|-------------------|
| Q8 vs Q4    | b0 c1  p=1.0000  | b4 c7  p=0.5488  | b4 c8  p=0.3877   |
| Q4 vs Q2    | b7 c0  p=0.0156  | b8 c0  p=0.0078  | b15 c0 p=0.0001   |
| Q8 vs Q2    | b6 c0  p=0.0312  | b8 c3  p=0.2266  | b14 c3 p=0.0127   |

### Osie (hard tier, repair=off) — surowo
(a) **ARITH** structure vs arith (10 par): Q8 0.30→0.10 (Δ+0.20); Q4 0.60→0.10 (Δ+0.50); Q2 0.40→0.00 (Δ+0.40). Arith ≈ podłoga na każdym quancie.
(b) **IQG** PL_EN(17) vs EN_EN(13): Q8 0.235 vs 0.462 (gap −0.226); Q4 0.353 vs 0.538 (−0.186); Q2 0.118 vs 0.231 (−0.113). EN_EN > PL_EN na każdym quancie.
(c) **Chain length** (2t:7 / 3t:6 / 4t:12 / 5t:5): Q8 0.71 / 0.00 / 0.08 / 0.80; Q4 0.86 / 0.50 / 0.25 / 0.20; Q2 0.43 / 0.33 / 0.00 / 0.00. Niemonotoniczne.

### Findingi (surowo)
1. Pełny gradient (n=45, hard n=30) daje moc, której n=7 nie miał: **Q4 vs Q2 istotne we wszystkich tierach** (p≤0.0156), **Q8 vs Q2 istotne all** (p=0.0127); **Q8 vs Q4 NIEistotne** (p≥0.39).
2. AQG Q8→Q4 dalej **ujemny/zerowy** (Q4 ≥ Q8 wszędzie: all 0.6222 vs 0.5333/0.6000) — trzeci raz z rzędu przeciwnie do H1.
3. Repair: Q8 +0.067 (hard +3 taski), Q2 +0.044 (easy +2), Q4 = 0 (identyczne). Niezerowy efekt repair (inaczej niż 22-task run, gdzie 0 dla obu).
4. Q2_K = ostra degradacja (all 0.29/0.33, hard 0.17, easy 1.0/0.93→0.53/0.67); avg_tok ~2× (13–18k vs 7–10k) → zapętla się do max_steps.
5. Arytmetyka = podłoga (≤0.10) vs structure 0.30–0.60 na n=10 par — failure w rozumowaniu na danych, nie w orkiestracji (potwierdza 22-task na większym n).
6. IQG ujemny: EN_EN > PL_EN na każdym quancie (gap 0.11–0.23) — interfejs PL trudniejszy mimo modelu PL-first.

## 2026-06-02 — Q3_K_M punkt gradientu + lokalizacja progu

### Cel
Dobicie JEDNEGO punktu między Q4 a Q2 (Q3_K_M) do lokalizacji progu. Tylko Q3, oba repair, 45 tasków = 2 runy.
Q8/Q4/Q2 NIE przeliczane (istniejące d6088b3). Świeży box Vast 4090 / CUDA 13.1 / driver 590.48.

### Setup
HEAD `d6088b3` CZYSTY (reset --hard po sync z lokalnego 1f066f0; jedyny diff = SESSION_LOG, kod/suite identyczne), tasks=45, pytest 204/204.
Q3_K_M = requantize z PUBLIC Q8_0 (`llama-quantize --allow-requantize ... Q3_K_M`, CPU-build llama.cpp `-DGGML_CUDA=OFF`):
3466 MiB / **3.89 BPW** (3.4G). Smoke PL koherentny (GPU offload CUDA0). llama-cpp 0.3.19 cu124 wheel + cu12 runtime + LD_LIBRARY_PATH.
Sanity gate easy-15 (repair=off): **13/15 = 0.867** (między Q2 0.53 a Q4 1.0, > 0.3 floor) → requantize OK.

### Run 2026-06-02 (commit d6088b3 clean, T=0 seed=42, RTX 4090)
`results/v3_full_2026-06-02/q3_{no_repair,repair}/`. Pass_rate off/on: **Q3 0.4222 / 0.4222** (19/45 oba; repair Δ0).
Kanoniczny pass/fail = `evaluate()`, cross-check vs summary.json num_passed = MATCH (Q8 24, Q4 28, Q3 19, Q2 13).

### Krzywa pass_rate per (quant × tier), repair=off — Q8→Q4→Q3→Q2
| quant   | easy (/15)   | hard (/30)   | all (/45)    |
|---------|--------------|--------------|--------------|
| Q8_0    | 14/15=0.933  | 10/30=0.333  | 24/45=0.533  |
| Q4_K_M  | 15/15=1.000  | 13/30=0.433  | 28/45=0.622  |
| Q3_K_M  | 13/15=0.867  |  6/30=0.200  | 19/45=0.422  |
| Q2_K    |  8/15=0.533  |  5/30=0.167  | 13/45=0.289  |
Q3 ląduje między Q4 a Q2 na all/easy; na hard Q3 (0.200) ≈ Q2 (0.167), poniżej Q8 (0.333) — niemonotonicznie.

### LOKALIZACJA PROGU — structure-only hard (n=20), repair=off
pass_rate: Q8 9/20=0.450 · Q4 12/20=0.600 · **Q3 5/20=0.250** · Q2 5/20=0.250.
McNemar exact (two-sided), pary sąsiednie (n10 = lepszy>gorszy, n01 = gorszy>lepszy; cross-check repo `paired_mcnemar` == niezależny exact-binomial):
| para         | n10 | n01 | p       | istotność |
|--------------|-----|-----|---------|-----------|
| Q4 ↔ Q3      | 7   | 0   | 0.0156  | **SIG**   |
| Q3 ↔ Q2      | 2   | 2   | 1.0000  | ns        |
| (ref) Q8 ↔ Q4| 4   | 7   | 0.5488  | ns        |
→ **Próg siedzi na Q4→Q3.** Q3 spadł już do poziomu Q2 (oba 5/20=0.250); Q3↔Q2 nieodróżnialne. Cliff: Q4(0.600) → Q3(0.250).

### Arith hard (n=10), repair=off
Q8 0.100 · Q4 0.100 · **Q3 0.100** · Q2 0.000. Podłoga arytmetyczna trzyma się na Q3 (1/10 = en_004_arith, Madrid single-temp 62.6). Arith nie niesie progu (brak miejsca na spadek).

### Finding (surowo)
Próg degradacji Q4→Q2 jest zlokalizowany na **Q4→Q3** (McNemar p=0.0156 na structure-20), nie Q3→Q2 (p=1.0000). Q3_K_M (3.89 BPW) zachowuje się na strukturze jak Q2_K, nie jak Q4_K_M — załamanie orkiestracji następuje już przy zejściu z 4-bit do 3-bit. Arith = podłoga na wszystkich 4 quantach.

## 2026-06-11 — Drabina L0-L3 + pełny gradient 67 tasków (Q8/Q4/Q3/Q2 × repair)

### Setup
Świeży box Vast 4090 (CUDA 13.0, driver 580.159.03, instance 40551707). HEAD **ef122d4 CZYSTY**, suite **67**
(15 easy + 52 hard = 30 chains + 12 v3_arith_L* + 10 B2-1). llama-cpp **0.3.19** cu124 wheel + cu12 runtime +
LD_LIBRARY_PATH (recipe). UWAGA: `hf` CLI nie wchodzi z `uv sync` — doinstalowane `huggingface_hub` 1.18 ręcznie.
Q8_0/Q4_K_M z HF (7.95/4.50 GB); Q3_K_M/Q2_K requantize z public Q8_0 (3.64/2.82 GB), smoke PL koherentny.
pytest 204/204 na boxie. **Gate easy-Q8 off: 14/15=0.9333 (reprodukcja)** → `gate_q8_easy/`. 8 runów T=0/seed42,
**scp po każdym quancie** (zero strat). Wszystkie summary: commit_hash=ef122d4 czysty; oracle `evaluate()` == num_passed 8/8.
Wyniki: `results/v3_ladder_2026-06-11/{q8,q4,q3,q2}_{no_repair,repair}/` + `analysis/{ANALYSIS.md,per_task_matrix.csv,analyze.py}`.

### Pass_rate (easy/hard/all), repair off → on
| quant   | easy (15)    | hard (52)    | all (67) off→on        |
|---------|--------------|--------------|------------------------|
| Q8_0    | 0.933/0.933  | 0.308→0.385  | 0.448 → 0.507          |
| Q4_K_M  | 1.000/1.000  | 0.385→0.385  | 0.522 → 0.522 (PEAK)   |
| Q3_K_M  | 0.867/0.867  | 0.269→0.269  | 0.403 → 0.403          |
| Q2_K    | 0.533/0.667  | 0.096→0.096  | 0.194 → 0.224          |
McNemar (off, all): Q4↔Q3 p=0.0215 SIG; Q3↔Q2 p=0.0013 SIG; Q8↔Q2 p=0.0005 SIG; Q8↔Q4 p=0.30 ns.
Próg dalej na Q4→Q3; kształt krzywej z runów 45-task replikowany na n=67. UWAGA: all-rate NIEporównywalne
wprost z 45-task (inny mianownik; drabina 12×0 ciągnie w dół).

### ★ DRABINA L0-L3 — rozstrzygnięcie zagadki arith (NIE-binarne)
Pass_rate: **0/48** (każdy poziom × każdy quant × off/on). Sama tabela poziomów NIE rozstrzyga — rozstrzyga
reklasyfikacja po treści final_answer (96 fail-slotów, `analysis/` sekcja 7):
**PROTOCOL_SHAPE 28** (głównie Q8: answer jako liczba/obiekt zamiast stringa — model LICZY ~dobrze, łamie schemat),
**GENUINE_ARITH 24** (Q3 najwięcej: 5/12 — liczba po prostu zła, np. L0 36.6/56.6/42.2 vs golden 45.97/49.57/45.03),
**TOOL_FIXATION/LOOP 21** (głównie Q2: na L0 woła narzędzia mimo danych w prompcie, pętli się do max_steps),
**ROUNDING_MINE 11+3** (poprawna procedura, średnia zaokrąglona do 1 miejsca przed konwersją: 7.76→7.8→46.04 itd. —
ta sama mina co stary en_013; goldeny drabiny .76/.76/.24 do naprawy wzorcem day2/day4 PRZED kolejnym runem drabiny),
MIXED 9. Wniosek: hipoteza "umie liczyć, gubi go łańcuch" NIE potwierdzona w czystej formie — L0 pada tak samo jak L3,
ale z INNYCH powodów per quant: Q8→protokół, Q3→arytmetyka, Q2→fiksacja narzędziowa. Quantyzacja przesuwa TRYB
porażki, nie tylko jej częstość.

### Length×język rozbity (B2-1; chains n=40, off)
short(2-3t): PL 0.67/0.89/0.89/0.22 vs EN 0.33/0.67/0.33/0.33 (Q8/Q4/Q3/Q2) — **PL > EN na short** (poza Q2).
long(4-6t): PL 0.15/0.23/0.08/0.00 vs EN 0.56/0.33/0.22/0.00 — **EN > PL na long** (Q8 wyraźnie).
Kierunek gapu językowego ODWRACA się z długością → wcześniejszy finding "EN_EN>PL_EN wszędzie" był konfundowany
długością łańcuchów. Q8 na 3-tool EN: 0/6 (anomalia do obejrzenia per-task).

### Repair (off↔on, McNemar all-67)
Q8 +4 (p=0.125 ns), Q2 +2 (p=0.50), Q4/Q3 Δ0. Spójne z historią (repair pomaga tylko na krańcach, nieistotnie).

### Box
Self-auth destroy NIE zadziałał na tym obrazie (klucz kontenerowy i ~/.vast_api_key → 401 Invalid user key;
CLI mimo błędu zwraca rc=0 — grepować output). Instancja 40551707 ubita RĘCZNIE przez usera z konsoli
2026-06-11; zweryfikowano connection refused. Lokalny vastai CLI bez klucza (403) — na przyszłość: klucz
usera albo ręczny destroy.

## 2026-06-18 — Clean-arith re-run (mina zaokrąglania USUNIĘTA, commit 83db813)

Po fixie miny (faa3bfa = drabina, 83db813 = wszystkie arith chainy + bliźniaki, wzorzec day2/day4):
pełne 67×8 (Q8/Q4/Q3/Q2 × repair off/on), RTX 4090 (instancja 41522333, host e3cfc6e849c2), CUDA 12.8,
llama-cpp-python 0.3.19 cu124 wheel + nvidia-cuda-runtime/cublas-cu12 + LD_LIBRARY_PATH (recipe). Q3_K_M/Q2_K
requantize z public Q8_0 (3.89/3.01 BPW), smoke PL koherentny. pytest 204. Gate easy-Q8 off=14/15=0.9333
(reprodukcja) → gate_q8_easy/. Wszystkie summary.json stemplowane commit_hash=83db813. T=0/seed42, scp po
każdym quancie. Wyniki: results/v3_arith_clean_2026-06-18/{q8,q4,q3,q2}_{no_repair,repair}/ + analysis/
{ANALYSIS.md, per_task_matrix.csv, analyze.py}. Tryby porażki z re-ewaluacji każdej trajektorii (evaluate()).

### Pass_rate (easy/hard/all), off → on
| Q8_0   | 0.933        | 0.308→0.462 | 0.448→0.567          |
| Q4_K_M | 1.000        | 0.365→0.481 | 0.507→0.597 (PEAK)   |
| Q3_K_M | 0.867        | 0.346       | 0.463 (repair Δ0)    |
| Q2_K   | 0.533→0.667  | 0.038       | 0.149→0.179          |
Bootstrap 95% CI all-67 off: Q8[.328,.567] Q4[.388,.627] Q3[.343,.582] Q2[.075,.239] (Q2 rozłączny).

### ★ MINA = 0 na każdym quancie (było 11+3=14 w b19ae0d) + tryb porażki PRZESUWA się z quantem
Arith+drabina (n=25, off) fails / PROTOCOL_SHAPE / GENUINE_ARITH / TOOL_FIXATION / ROUNDING_MINE:
Q8 21/16/4/1/0 · Q4 21/7/13/1/0 · Q3 20/5/4/11/0 · Q2 25/6/15/4/0.
Po usunięciu miny widać czysto: **Q8→protocol-shape, Q4→genuine-arith, Q3→tool-fixation, Q2→collapse**.
To główny finding — progresja wcześniej maskowana przez minę (14 fałszywych faili „poprawna-wartość-odrzucona").

### Arith floor (twin struktura vs arith wartość, matched n=10, off)
Q8 .20/.20 · Q4 .40/.20 · Q3 .40/.20 · Q2 .10/.00. Wartość = ścisła podłoga pod orkiestracją
(Q4/Q3 rozwiązują łańcuch 2× częściej niż trafiają liczbę). Drabina L0–L3 ≈ 0/3 na każdym poziomie/quancie.

### McNemar (off) — KLIF na Q3→Q2, NIE Q4→Q3
hard-52: q8-q4 p=.549 · q4-q3 p=1.000 · q3-q2 **p<.0001** (b=16,c=0).
structure-chain-27: q4-q3 p=.727 · q3-q2 **p=.0010**. Próg b19ae0d „Q4→Q3" (structure-20, p=.0156) NIE
reprodukuje po fixie miny — Q4≈Q3 statystycznie, ostry monotoniczny collapse jest na 3-bit→2-bit.
Caveat: fix ruszył też miasta/dni części bliźniaków strukturalnych → nie 1:1 z structure-20 z 2026-06-11.

### Length×język (chains, off) — surowo
short PL (L2/PL n=9) twarde: 7/9/9/1 (Q8/Q4/Q3/Q2); long PL order-trap (L4/PL n=11) = podłoga 0/1/2/0;
long EN (L5/EN n=7) mocne na Q8 (5/7), degraduje 2/1/0. Czysta „PL>EN short / EN>PL long" rozmyta przez
nierówne kubełki po rebalansie miast/dni — dominująca podłoga to rodzina long-PL order-trap.

### Box
Instancja 41522333 — self-auth destroy próbowany na końcu (znana odchyłka tego obrazu: 401, rc=0 mimo błędu).

## 2026-07-11 — 11B dense-curve: Bielik-11B-v3.0-Instruct, 6 quantów × repair off/on × 67 tasków

Pierwszy run 11B (dense, nie Minitron): DevQuasar/speakleash.Bielik-11B-v3.0-Instruct-GGUF — JEDNO źródło
statycznych quantów Q8_0→Q2_K, zero requantize. Box 4090/CUDA 12.6 (instancja 42274707, host 831842528a85;
box NIE-świeży: pre-provisioned Q8 gguf + leftover lexpilot-demo, nietknięty), recipe cu124 wheel 0.3.19 +
cu12 runtime libs. HEAD a023c3b clean (67 YAML), pytest 204, smoke PL koherentny na KAŻDYM quancie (nawet Q2).
T=0/seed42, chatml; stemple commit_hash=a023c3b 12/12; oracle evaluate()==summary.num_passed 12/12; scp po
każdym quancie. Wyniki: results/v3_11b_2026-06-18/{q8,q6,q5,q4,q3,q2}_{no_repair,repair}/ + analysis/
{ANALYSIS.md, per_task_matrix.csv, analyze.py} + box_logs/. Gate easy-Q8 off 14/15=0.9333 — ta sama liczba
i ten sam fail (adv_005) co 7B.

### Krzywa (easy | hard | all, off→on)
Q8_0 0.933 | 0.769 | 0.806 (on =) · Q6_K 1.000 | 0.788→0.808 | 0.836→0.851 (PEAK) · Q5_K_M 0.867 |
0.712→0.731 | 0.746→0.761 · Q4_K_M 0.867 | 0.442→0.519 | 0.537→0.597 (DIP) · Q3_K_M 0.800 | 0.692 |
0.716 (Δ0) · Q2_K 0.133 | 0.019→0.058 | 0.045→0.075 (COLLAPSE).
11B >> 7B clean na każdym wspólnym quancie POZA Q2 (7B all-off: .448/.507/.463/.149) — Q2 11B GORSZY od 7B.

### ★ DIP Q4 zamiast peaku Q4 — obustronnie SIG
Q5>Q4 p=.0043 (hard 17:3, p=.0026) i Q3>Q4 p=.029 (hard 17:4, p=.0072) — 7B-owy „Q4 peak" ODWRACA się w dip.
14 tasków Q4-specyficznych (fail@Q4-off, pass@Q5-off i @Q3-off): dominują PL_EN 4-tool order-trapy, tagi
wrong_tool_order + final_answer_missing/unknown_action. Największy efekt repair na krzywej: +4 (p=.125 ns),
ratuje 3/14; runner timeouts Q4 off=14 vs 3-6 u sąsiadów. Wygląda na idiosynkrazję artefaktu Q4_K_M DevQuasar
dla 11B, nie własność 4-bit per se — do papera: jeden punkt siatki ≠ kształt krzywej.

### Klif Q3→Q2 jak w 7B clean, ale kolaps o INNEJ sygnaturze
Q3→Q2 p<.0001 (46:1). Q2 off: 64/67 faili; wrong_tool_order:46, wrong_final_answer:21, unknown_action:13;
śr. kroków 2.8 (pozostałe quanty ~4.4-4.7), max_steps tylko 8/67, avg tokens 5397 < Q8 6729 → SZYBKA ŚMIERĆ
(malformed/unknown action na starcie, brak recovery), NIE pętle-do-max_steps jak 7B (~2× tokens). Smoke Q2
nadal koherentny — kolaps jest agentic-specific, nie językowy.

### Tryby porażki ARITH+DRABINA n=25 (off; klasyfikator 1:1 z clean 7B; ROUNDING_MINE=0 wszędzie ✓)
11B fails/PS/GA/TF: Q8 11/5/4/2 · Q6 10/3/5/2 · Q5 11/4/6/1 · Q4 17/9/7/1 · Q3 10/0/7/3 · Q2 25/5/19/1.
7B clean: Q8 21/16/4/1 · Q4 21/7/13/1 · Q3 20/5/4/11 · Q2 25/6/15/4. Progresja 7B (Q8→shape, Q4→arith,
Q3→fixation, Q2→collapse) NIE reprodukuje się czysto w 11B: top-quanty mieszają PS/GA przy niskim TF,
Q4→shape-spike (PS=9), Q3→czysty GENUINE_ARITH (PS=0!), Q2→GA nominalnie (klasyfikator ARITH-first; realnie
total orchestration collapse). Quantyzacja 11B przesuwa tryb porażki ŁAGODNIEJ niż w 7B.

### Drabina L0–L3 — GRADIENT ODWRÓCONY (arith floor tylko na L0)
off (Q8/Q6/Q5/Q4/Q3/Q2): L0 0/0/0/0/0/0 z 3 · L1 0/1/1/0/3/0 · L2 1/0/0/0/1/0 · L3 3/3/3/0/2/0.
11B rozwiązuje PEŁNY łańcuch L3 (3/3 na Q8/Q6/Q5), a pada na L0 bez narzędzi — odwrotność hipotezy „tonie
w scaffoldingu"; 7B miał 0/3 na każdym poziomie. Arith w izolacji (L0) = podłoga niezależna od quanta.
Drabina łącznie: Q8/Q6/Q5 4/12, Q3 6/12 (najlepsza!), Q4 i Q2 0/12. Repair: tylko Q4-L3 0→2.

### Twin matched n=10 (struct/arith, off)
Q8 1.00/.80 · Q6 1.00/.90 · Q5 .90/.80 · Q4 .50/.60 (jedyna inwersja) · Q3 .90/.70 · Q2 .00/.00
(7B clean: .20/.20 · .40/.20 · .40/.20 · .10/.00). Struktura ≥ arith poza dipem Q4; headroom 11B vs 7B ogromny.

### Length×język (chains n=40, off, Q8→Q2)
short PL 1.00/1.00/1.00/.89/.78/.00 · short EN .78/.89/.67/.78/.89/.00 · long PL 1.00/.92/.92/.31/.77/.08 ·
long EN .78/.89/.67/.44/.56/.00. 7B-owa inwersja „EN>PL na long" NIE występuje na zdrowych quantach 11B
(PL≥EN na Q8/Q6/Q5 również na long); pojawia się DOPIERO w dipie Q4 (long PL .31 < EN .44) → inwersja gapu
była sygnaturą degradacji modelu, nie własnością suity.

### Box
Self-auth destroy ZADZIAŁAŁ na tym obrazie: `vastai destroy instance 42274707` → „destroying instance …",
bez 401 w outpucie; reconnect po 20 s → connection refused. (Refused ≠ dowód — potwierdzić w panelu, że
instancja zniknęła z listy.) Logi runów i skrypty zabezpieczone w results/v3_11b_2026-06-18/box_logs/.

---

## 2026-07-29 — RUN NOCNY: PLLuM + extended ladder + wariancja (HEAD e584b38, box 46147751, RTX 4090)

Autonomiczny run nocny 22:53–02:39. **52 runy zapisane** (26 z planu + 2 bramkowe + 24 bonusowe),
wszystkie zescp-owane i zweryfikowane przed skasowaniem modelu. Pełny przebieg minutowy z każdą
decyzją: `results/NIGHT_LOG.txt` (200 linii, 7 ALERTÓW). Wszystkie liczby to `num_passed/num_tasks`
z `summary.json` (oracle), nie flaga `trajectory.success`.

Środowisko: RTX 4090 24 GB, CUDA 12.6, llama-cpp-python **0.3.19** (prebuilt cu124 + cu12 runtime libs),
n_ctx 8192, T=0 seed 42 poza FAZĄ 5. Bramki FAZY 0 zielone: HEAD czysty, 67 adversarial + 46 ladder_ext,
pytest 204. VRAM 24 GB ≥ 20 → plan pełny. `src/` i `tasks/` nietknięte przez całą noc.

### FAZA 1 — PLLuM-8B: BRAMKA C NIEZDANA, faza pominięta regułą
Bramka A czysta (poprawna polszczyzna, `finish=stop`, zero artefaktów `llama-3`). Bramka B: peak
**2308** prompt-tokenów na najdłuższym łańcuchu suity (10-krokowy `v3_chain_en_013`; trzy 8-krokowe L3
dały 1130–1474) → poniżej progu 7000, **n_ctx został 8192**, żadnej asymetrii wobec Bielika.
Bramka C (easy 15): **0.400 (6/15) off, 0.467 (7/15) on** — obie poniżej 0.5.

Zdiagnozowane przed wykonaniem reguły — **to nie jest wada konfiguracji**: zrenderowany przez handler
`llama-3` prompt zawiera nienaruszony słownik akcji (`call_tool`/`final_answer`) i pełną listę narzędzi
(zweryfikowane inspekcją `res.prompt`). Model mimo to emituje `{"action":"send_weather_alert"}` zamiast
`{"action":"call_tool","tool":"send_weather_alert"}` → `unknown_action`. Następnie **halucynuje sukces**:
`final_answer` twierdzi, że alert wysłano, przy `alerts_sent=[]`. Stąd rozjazd `trajectory.success` 14/15
vs oracle 6/15 — kolejne potwierdzenie, że flaga runnera przeszacowuje i kanoniczny jest oracle.

### FAZA 2 — ladder_ext na 11B (8 runów) — ranking zanieczyszczony typowaniem JSON
off/on: **Q8_0 13/13 · Q4_K_M 1/7 · Q3_K_M 32/32 · Q2_K 0/0** (z 46).

Q3 bije Q8 o 19 zadań, ale **nie należy tego czytać jako miary zdolności**. 100 % naruszeń schematu to
JEDEN wzorzec: model zwraca `{"action":"final_answer","answer": 54.2}` — **liczbę zamiast stringa** —
i pydantic odrzuca (`tagged-union[CallTool,FinalAnswer]`, `answer: string_type`). Skala: Q8_0 = **101
naruszeń w 23 z 46 zadań** (~70 % jego porażek), Q4_K_M = 119 w 27 zadaniach, Q3_K_M = **0**. `repair`
tego nie naprawia (q8_repair: identyczne 101, wynik bez zmian).
**Ostrzeżenie:** to NIE są darmowe punkty. Kontrprzykład `v3_ext_L1_b`: golden 48.2, Q8 odpowiedział 54.2
— liczba też merytorycznie zła. Podział SKRÓT (format) vs PRAWDZIWY (treść) = etap analizy; `raw_model_output`
każdego kroku jest zachowany, więc tolerancyjne przeliczenie zrobi się offline, **bez powtarzania na GPU**.

### FAZA 3 — ladder_ext na 7B (8 runów)
off/on: **Q8_0 2/3 · Q4_K_M 1/9 · Q3_K_M 2/2 · Q2_K 0/0** (z 46). Q3_K_M i Q2_K przez requantize z Q8_0
(`llama-quantize` CPU-only, recepta z poprzednich runów). Krzywa 7B na ladderze leży płasko przy zerze —
brak odpowiednika skoku Q3, który widać na 11B.

### FAZA 4 — main suite na 7B, Q6_K i Q5_K_M (4 runy)
off/on: **Q6_K 31/38 · Q5_K_M 35/40** (z 67). **Korekta do promptu:** repozytorium
`speakleash/Bielik-Minitron-7B-v3.0-Instruct-GGUF` **zawiera** publiczne Q6_K i Q5_K_M. Requantize byłby
odstępstwem od metodologii oryginalnej krzywej 6-punktowej (2026-06-02), która też wzięła Q6/Q5 z release'u
HF — użyto plików publicznych. Q5 > Q6 to kolejna niemonotoniczność, zgodna z historycznym szczytem przy Q4.

### FAZA 5 — wariancja przy T=0.7 (6 runów): rozkład DWUMODALNY, nie szum
11B, main 67, repair off:
- **Q8_0**: seed1 **8/67** (0.119) · seed2 **49/67** (0.731) · seed3 **48/67** (0.716)
- **Q3_K_M**: seed1 **13/67** (0.194) · seed2 **43/67** (0.642) · seed3 **51/67** (0.761)

Efekt seed=1 jest **systematyczny**: zapada się na OBU kwantach niezależnie, seedy 2 i 3 na obu dają
0.64–0.76. Mechanizm widać w błędach parsowania (Q8): seed1 `unknown_action=109`, `no_json_found=12`,
`schema_violation=20`; seed2 odpowiednio `22 / 4 / 11`. Model wpada w tryb **wymyślania nazw akcji** —
ten sam defekt, który zabił PLLuM na bramce C, u Bielika ujawnia się dopiero pod próbkowaniem.
**Nie raportować średniej** (Q8: 35/67) — nie opisuje żadnego z dwóch trybów.
Trop do sprawdzenia (hipoteza, kodu NIE zmieniano): `llama_cpp_runner.py` podaje ten sam seed do
`create_chat_completion` przy KAŻDYM kroku pętli, a nie raz na run — pechowa wartość może utrwalać się
przez całą trajektorię zamiast się uśredniać.

### BONUS (poza planem) — pełna krzywa PLLuM-8B, 24 runy
Uruchomiona **po** zamknięciu faz 2–5, z zapasu czasu, po niezdanej bramce C. Katalogi opisane w
`results/v3_pllum_2026-07-29/BONUS_README.txt`, żeby nie czytać ich jako realizacji FAZY 1.
main 67 off/on: **Q8 13/15 · Q6 12/14 · Q5 7/9 · Q4 15/17 · Q3 15/18 · Q2 1/1**.
ladder 46 off/on: **Q8 2/2**, wszystkie pozostałe kwanty **0/0**.
PLLuM na main trzyma się w paśmie 0.10–0.27 tam, gdzie 7B daje 0.46–0.60 — rząd wielkości niżej.

### Wzorzec przekrojowy: repair działa tylko w wąskim paśmie Q4
Ladder, zysk z `--repair`: 11B Q8 +0, **Q4 +6**, Q3 +0, Q2 +0 · 7B Q8 +1, **Q4 +8**, Q3 +0, Q2 +0.
Powtarza się na dwóch niezależnych modelach: naprawa nie pomaga ani gdy model trzyma format (Q8/Q3),
ani gdy jest już rozłożony (Q2) — tylko tam, gdzie psuje się składnia, a treść jeszcze żyje.

### Do etapu analizy (nie robione tej nocy)
1. Tokeny **nie są porównywalne** między Bielikiem a PLLuM (różne tokenizery) — porównania
   międzyrodzinowe raportować w KROKACH.
2. Fail L3N dzielić na SKRÓT i PRAWDZIWY, dwie pass raty (ścisła i tolerancyjna).
3. `summary.json` **nie zapisuje** pól `seed` ani `temperature` na najwyższym poziomie (oba `None`) —
   przypisanie runu do seeda idzie WYŁĄCZNIE z nazwy katalogu (`q8_seed1/2/3`).

### Usterki nocy
- **Błąd w harnessie nocnym (mój, nie w repo):** `note()` w `night/lib.sh` pisało na stdout, więc
  `MP=$(fetch_model …)` wciągnęło linię logu do ścieżki modelu → pierwszy start FAZY 2 padł na
  `ValueError: Model path does not exist`. Naprawione (stderr), model był pobrany poprawnie, zero
  utraconych obliczeń.
- Żaden run nie padł merytorycznie; 52/52 mają `summary.json`.

---

## 2026-08-21 — TRZY SESJE ANALITYCZNE OD BIURKA (zero GPU, box nie istnieje)

Powrót do projektu po miesiącu. Trzy sesje tego samego dnia, wszystkie wyłącznie na danych
z dysku: `results/**/run.log`, `results/**/trajectories.jsonl`, `results/**/summary.json`,
`tasks/**/*.yaml`. Żadnego GPU, żadnego boxa, żadnej sieci. **Skrypty odtwarzające każdą liczbę
leżą w `analysis/`** (commit `ccc0d87`), mapa skrypt → tabela → finding jest w
`analysis/README.md`. Tabele nie są tu kopiowane — ten wpis to decision trail, liczby produkują
skrypty.

### Sesja 1 — stan po runie nocnym i zabezpieczenie danych

**Pytanie:** ile z planu nocnego 2026-07-29 faktycznie się policzyło i zostało lokalnie?
**Skrypt:** `analysis/inventory.py`

**Ustalenie: run nocny SIĘ DOKOŃCZYŁ**, wbrew założeniu, z którym wracałem. 52/52 runy mają
kompletny `summary.json` z `commit_hash=e584b38`, `trajectories.jsonl` nie są urwane (ostatnia
linia parsuje się jako JSON w 52/52), a każda para `NN/MM` zgadza się w obie strony z
`results/NIGHT_LOG.txt` (200 linii, 52 linie wynikowe). Bramki bez zmian: 67 adversarial,
46 ladder_ext, pytest 204.

★ **Jedyne realne ryzyko dnia było operacyjne, nie naukowe:** `results/` jest w `.gitignore`
(linia 55), a repo nie miało remote'a — 29 MB wyników istniało dokładnie w jednym miejscu
i zwykły `git clean -xfd` skasowałby je bez śladu. Domknięte tego samego dnia, patrz
"Stan po sesji".

### Sesja 2 — trzy anomalie z runu nocnego

#### Anomalia 1 — PLLuM 0.194 przy Q8, gdy Bielik-11B daje 0.806

**Pytanie:** zepsuty szablon czy model faktycznie tak słabo radzi sobie z zadaniem?
**Skrypty:** `analysis/pllum_raw_dump.py`, `pllum_patterns.py`, `pllum_vs_bielik.py`,
`pllum_ceiling.py`

**Werdykt: to nie jest zepsuty szablon — model mówi naszym protokołem i mimo to nie umie
zadania.** Zero artefaktów szablonu po obu stronach (`<|..|>`, `[INST]`, `<s>`, nagłówki ról).
83,9 % kroków PLLuM parsuje się poprawnie wobec 89,3 % u Bielika — różnica 5,4 pp, nie przepaść.
Rozkład tagów jest **odwrócony**: PLLuM 74 wystąpienia tagów treściowych wobec 29 formatowych,
Bielik 15 wobec 43. Liczba zamykająca: nawet po darowaniu PLLuM **każdej** porażki dotkniętej
błędem formatu sufit wynosi **32/67 = 0.478**, poniżej faktycznego 0.806 Bielika, a 35 z 54
porażek nie ma błędu formatu w ogóle.

Wady własne PLLuM, do opisania w paperze osobno od wyniku: spłaszczona koperta (nazwa narzędzia
w polu `action`), symulowanie wyniku narzędzia we własnym wyjściu (17,2 % kroków), 2,60 kroku
na trajektorię wobec 4,58 u Bielika. `adv_010` = model porzuca protokół i prowadzi uprzejmą
rozmowę z samym sobą przez cztery kroki.

#### Anomalia 2 — seed 1 daje 8/67, seedy 2 i 3 dają 49 i 48

**Pytanie:** czy run wystartował poprawnie, czy trajektorie są urwane/puste/merytorycznie złe
i czy seed w ogóle trafił do konfiguracji?
**Skrypty:** `analysis/variance_seed_config.py`, `variance_classify.py`, `variance_repetition.py`

**Werdykt: run wystartował poprawnie, seed trafił do konfiguracji, trajektorie nie są ani
urwane, ani puste — zapaść jest w dyscyplinie koperty, nie w rozumowaniu.** Seed i temperatura
SĄ w rekordach trajektorii (1/2/3 przy T=0.7), więc przypisanie po nazwie katalogu jest
potwierdzone niezależnie danymi, mimo `None` w `summary.json`. Seed1 wyprodukował **więcej**
tekstu (472 692 tokeny wobec 419 324) i pracował **dłużej** (417 s wobec 274 s) niż seed2, który
punktuje sześć razy lepiej. Różnica siedzi w jednym miejscu: 44,2 % kroków seed1 nie parsuje się
wobec 13,0 % w seed2. ★ **Po darowaniu kaskad formatu seed1 ląduje na 0.776 (Q8) i 0.881 (Q3)**,
czyli w tym samym paśmie co faktyczne wyniki seedów 2 i 3.

Fakt o kodzie potwierdzony w źródle (nie hipoteza): `llama_cpp_runner.py:292` — konstruktor
`Llama(...)` **nie dostaje seeda w ogóle**, a `create_chat_completion(seed=seed)` w linii 311
dostaje ten sam seed przy **każdym** kroku pętli (wołane z linii 103, ze środka
`for step_idx in range(task.max_steps)`). Co ten parametr robi wewnątrz llama-cpp — nadal
nierozstrzygnięte, biblioteki nie ma w tym venvie.

#### Anomalia 3 — drabina, rozbicie na szczeble

**Pytanie:** pass rate osobno dla L0/L1/L2/L3T/L3N na obu Bielikach i każdym kwancie; dla L3N
podział porażek na SKRÓT i PRAWDZIWY oraz dwie raty, ścisła i tolerancyjna.
**Skrypty:** `analysis/ladder_rungs.py`, `ladder_breakdown.py`, `ladder_nearmiss.py`,
`ladder_typing_tolerant.py`, `ladder_controls.py`

**Werdykt: przewidywany SKRÓT nie istnieje, a bliskie porażki L3N to wyłącznie typowanie pola
`answer`.** Model wykonuje wymagany łańcuch (`get_weather > get_forecast > convert > convert`)
i podaje golden, po czym odpada, bo `answer` jest floatem (11B) albo dictem (7B) przy schemacie
wymagającym stringa. Rata tolerancyjna liczona wg **faktycznej** przyczyny: L3N na 11B Q8 idzie
**0.20 → 0.90**, na 7B Q8 **0.00 → 0.70**.

★ **L0 = 0.00 we wszystkich ośmiu runach, ale z dwóch różnych przyczyn** — to nie jest jedno
zjawisko: 11B łamie zakaz wywołań narzędzi (`unexpected_tool_call` ×10), a 7B i Q2 są posłuszne,
tylko psują kopertę albo liczą źle. Kontrola „to nie są darmowe punkty" przeszła:
L1 i L2 mają identyczne tagi formatu, ale golden jest tam **nieobecny** (model odpowiada 59
zamiast 46.4, 54.2 zamiast 48.2), więc nie zostały darowane — `ladder_controls.py`.

### Sesja 3 — trzy analizy pogłębiające

#### Analiza 1 — anatomia dipu Q4 na Bielik-11B (main 67, repair off)

**Pytanie:** czy dip Q4 (0.537 wobec 0.746 na Q5) przeżyje darowanie kaskad formatu, czy zniknie;
i czy zadania padające tylko na Q4 to spójna grupa?
**Skrypty:** `analysis/q4dip_classify.py`, `q4dip_depth.py`, `q4dip_deep_ceiling.py`,
`q4dip_group.py`

Uwaga metodologiczna: `results/v3_11b_2026-06-18/` (commit `a023c3b`) **nie ma `run.log`**,
więc werdykty odtwarzane są kodem repo (`eval.smoke.evaluate`). Legalizuje to fakt, że
`tasks/adversarial/` i `src/polagentbench/eval/` są bajt w bajt identyczne między `a023c3b`
a HEAD. Odtworzenie zwalidowane w dwie strony — 48/36/50 zgodne z `summary.json` **i** z
`analysis/per_task_matrix.csv`, zero rozjazdów.

**Werdykt: dip Q4 przeżywa darowanie kaskad formatu, ale traci ponad połowę wielkości** — z
−0.209 do −0.090 wobec Q5 na całej suicie i z −0.520 do −0.320 w kubełku, w którym faktycznie
żyje. To złożenie obu przyczyn, mniej więcej 57:43 na korzyść formatu. Grupa 14 zadań padających
tylko na Q4 **nie jest losowym rozrzutem**: 79 % ma co najmniej cztery wywołania przy 37 %
w suicie, 86 % wymaga `convert_temperature`, 6 z 14 ma bajtowo identyczną sygnaturę tagów,
a w drugą stronę idzie jedno zadanie (`adv_004b`).

★ **Cały dip siedzi na głębokości ≥4 wywołań** (0.32 wobec 0.84 na Q5); przy 2–3 wywołaniach Q4
jest **wyżej** niż Q5 i Q3. Zdanie do papera: dip Q4 to degradacja dyscypliny koperty, która
ujawnia się dopiero powyżej trzech wywołań narzędzi i tam zamienia się w niedokończone łańcuchy
i timeouty (87 udanych `call_tool` wobec 127 na Q5, jedenaście razy więcej spłaszczonych kopert).

#### Analiza 2 — skąd się bierze „59"

**Pytanie:** cztery zadania L1 odpowiadają 59 — kotwica z kontekstu czy atraktor spoza kontekstu?
**Skrypty:** `analysis/attractor59_cases.py`, `attractor59_count.py`,
`attractor59_negative_controls.py`, `attractor59_direction.py`

**Werdykt: atraktor spoza kontekstu, nie kotwica z kontekstu.** We wszystkich czterech zadaniach
model wykonuje poprawny łańcuch i dostaje z narzędzia wartości, których średnia jest **dokładnie
goldenem** — a odpowiada 59 i powtarza to aż do `max_steps`. Trzy różne goldeny, trzy różne pary
wartości wejściowych, ta sama odpowiedź. Kontrole negatywne: 59 nie jest goldenem **żadnego**
zadania w suicie, nie występuje w `environments/weather.py`, a 15 °C w ogóle nie istnieje wśród
temperatur środowiska (zakres −5.0 … 19.0).

★ **59 °F = 15 °C dokładnie** — kanoniczna para z tablic przeliczeniowych. 59.0 jest najczęstszą
liczbową odpowiedzią w **całym** zbiorze: 91 par (run, zadanie), 26 zadań, 23 runy, oba modele,
pięć poziomów kwantyzacji. Kierunek przyczynowy rozstrzygnięty: z 91 przypadków zero ma 59
w promptcie, jedenaście ma je w wyniku narzędzia — i we **wszystkich jedenastu** dlatego, że
model sam podał narzędziu `convert_temperature(value=15, …)`. Do papera: **fallback na pamięć
parametryczną przy poprawnie wykonanym łańcuchu narzędzi** — najbardziej niepokojąca odmiana
błędu, bo trajektoria wygląda na wzorową aż do ostatniego kroku.

#### Analiza 3 — rozdzielenie zmiennych w envelope collapse

**Pytanie:** czy spłaszczanie koperty jest efektem narzędzia (`convert_temperature`), czy pozycji
w łańcuchu (trzeci krok) — a jeśli obie zmienne są skonfundowane, zapisać to jako limitation.
**Skrypty:** `analysis/envelope_positions.py`, `envelope_marginals.py`

**Werdykt: zmienne się rozdzielają, konfundacji nie ma, i dominuje narzędzie.** Oba warunki
rozstrzygające spełnione z zapasem: 14 wywołań `convert` poza trzecim krokiem, z czego **8 ma
poprawną kopertę**, oraz 27 trzecich kroków bez `convert`, z czego **26 ma poprawną kopertę**.
Iloraz ryzyka: **narzędzie 3.95×** (50,0 % wobec 12,7 %), **pozycja 0.60×** — trzeci krok jest
wręcz *bezpieczniejszy* od średniej.

Kontrast wart osobnego zdania: u Bielika-7B **żadna** z dwóch zmiennych nie tłumaczy niczego
(0.73× / 1.13× dla narzędzia, 0.81× / 0.74× dla pozycji przy 30–40 % złych kopert w tle) —
tam rozsypka koperty jest rozproszona po całym runie. Limitation, która zostaje: komórka
„trzeci krok + convert" ma liczebność 2; wniosek nie opiera się na niej, tylko na rozkładach
brzegowych 16/158 i 29/145.

### Obalone po drodze

Cztery rzeczy, w które wierzyliśmy przed tym dniem, a które dane obaliły. Zapisane, żeby nie
wracały:

1. **Hipoteza zaklinowanego samplera — OBALONA.** Wniosek z runu nocnego, że seed podawany co
   krok „zaklinowuje" model w pętli, nie broni się w danych. Sygnatura zapętlenia (powtórzone
   wyjścia w obrębie trajektorii) **nie wyróżnia seed1**: najwięcej powtórzeń ma **seed3
   (13,7 %), który daje 48/67**; seed1 ma 6,3 %, praktycznie tyle co seed2 (6,5 %). Fakt o kodzie
   (seed podawany przy każdym kroku) zostaje, ale przestaje być wyjaśnieniem zapaści.
   `analysis/variance_repetition.py`.
2. **Kategoria SKRÓT — PUSTA.** Plan zakładał, że część porażek L3N to skrót: poprawny golden
   przy jednej konwersji zamiast dwóch. W danych **0 z 80** zadań L3N. Modele robią albo dwie
   konwersje (poprawna liczba), albo zero, albo sześć — jednej nie robi nikt. Rata tolerancyjna
   w tej definicji równa się ścisłej i sama w sobie nic nie wnosi; wartość ma dopiero rata
   liczona wg typowania. `analysis/ladder_breakdown.py`.
3. **`attractor59_scan_raw.py` ZAWYŻA.** Pierwszy skan liczył każdy obiekt JSON osobno, a model
   powtarza tę samą odpowiedź przez wiele kroków — stąd `61` wychodziło 4189 razy przy 32
   faktycznych parach (run, zadanie). Skrypt zachowany, bo to on wykrył, że czołówka odpowiedzi
   to dokładne konwersje C→F, ale **oznaczony w docstringu i README jako niebędący źródłem
   liczb**. Liczby raportowane pochodzą z `attractor59_count.py`, który deduplikuje w obrębie
   trajektorii.
4. **Korekta targetowania envelope collapse.** Dokument przekazania mówił, że 18 wystąpień
   spłaszczonej koperty dotyczy **Bielika-7B Q8 na main** — to było **błędne**. W danych żaden
   run 7B Q8 na main nie ma 18 wystąpień (mają 31 i 50); jedynym runem `main67` z dokładnie 18
   jest **PLLuM-8B Q8**. Analiza 3 poszła na PLLuM, oba runy 7B dołożone jako kontrast.
   Wykryte przez `analysis/inventory.py` — stąd reguła: **puszczać inwentarz przed każdą nową
   analizą, zanim policzy się cokolwiek na niewłaściwym runie.**

### Decyzje produktowe dnia

- **Mina typowania — rozwiązana opcją 1: obie raty jako sensitivity analysis.** Nie wybieramy
  między ratą ścisłą a tolerancyjną i nie zmieniamy schematu post hoc. Paper raportuje obie
  obok siebie, z jawnym opisem, że różnica to wyłącznie typ pola `answer`, oraz z kontrolą
  `ladder_controls.py` pokazującą, że tolerancja nie rozdaje darmowych punktów (L1/L2 nie są
  darowane, bo golden jest tam nieobecny).
- **PLLuM wchodzi do papera jako pełnoprawny trzeci model**, nie jako przypis ani materiał
  odrzucony. Z jawnym **disclosure o bramce C**: krzywa PLLuM powstała jako BONUS po niezdanej
  bramce (0.400 / 0.467 przy progu 0.5), a nie jako realizacja FAZY 1 planu nocnego. Uzasadnienie
  merytoryczne dla włączenia: sufit hojny 0.478 pokazuje, że niski wynik jest pomiarem zdolności,
  a nie awarią konfiguracji.
- **Tytuł papera:** „The Q2 Cliff: Agentic Degradation Under GGUF Quantization in Three Polish
  Open Models".

### Stan po sesji

- Skrypty analityczne w `analysis/` (24 pliki + README z mapą), commit `ccc0d87`, wszystkie
  wyłącznie do odczytu, wszystkie zielone z katalogu głównego repo.
- **Dane zabezpieczone poza maszyną**, domknięcie ryzyka z Sesji 1: prywatne repo
  `JakubPrejzner/polagentbench` oraz release `backup-20260821` z `results_20260821.tar.gz`
  (327 plików, sha256 `2d58004686…`) i manifestem per-plik. Kopia zweryfikowana round-tripem:
  pobrana z GitHuba rozpakowuje się do 327/327 plików zgodnych z manifestem sprzed pakowania.
- `results/` pozostaje gitignorowane i **nie jest** w repo — surowe dane żyją w releasie
  i w `polagentbench-backup/` na dysku.
