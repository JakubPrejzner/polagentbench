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
