# PolAgentBench

A Polish-first benchmark for measuring what GGUF quantization does to **agentic tool use** —
calling the right tools in the right order and computing correct answers from their outputs —
in a realistic non-English setting: Polish prompts against English tool schemas.

Three models, six precisions each (Q8_0 down to Q2_K), 113 deterministic tasks.
This repository holds the benchmark, the trajectories used in the released analysis, the per-task outcome
matrices, the failure classifier, and the analysis scripts behind the paper.

Companion paper: `paper/polagentbench_paper.tex` —
*Quantization Thresholds Replicate, Failure Modes Do Not: A Three-Model Study of Agentic
Tool Use in Polish from 8-bit to 2-bit*.

## Models under test

| label | model | role |
|---|---|---|
| `bielik-11b-v3` | Bielik-11B-v3.0-Instruct | parent |
| `bielik-minitron-7b-v3` | Bielik-Minitron-7B-v3.0-Instruct | pruned + distilled child of the above |
| `llama-pllum-8b` | Llama-PLLuM-8B-instruct | separate pretraining family, comparable scale |

The Bielik pair isolates **model compression** as a package of structural pruning,
distillation, and the child's own post-training, sharing lineage, corpus, and tokenizer.
Those components and parameter count are not separable in this pair. PLLuM adds the
**pretraining-family** axis at comparable scale while staying a Polish-focused model.

## Five results

1. **The collapse threshold replicates across all three models.** Every model falls off a
   cliff between 3-bit and 2-bit: 11B `0.716 → 0.045`, 7B `0.463 → 0.149`, PLLuM
   `0.224 → 0.015`. Paired exact McNemar gives `p < 0.0001` for both Bieliks and
   `p = 0.00012` for PLLuM — across a fourfold spread in absolute capability, across
   compression by pruning plus distillation, and across a change of pretraining family.

2. **Failure modes do not replicate. Three models, three signatures.** At 2-bit the 7B
   fails long (median 9,139 tokens over 4 steps), mostly still producing a parsed final
   answer (38/57 failures); its predominant budget exhaustion belongs to 3-bit (27/36
   failures, median 26,833 tokens over 8 steps). The 11B at 2-bit fails short (median
   1,506.5 tokens and one step); 37/64 failures emit a well-formed final answer at the
   first step. PLLuM fails on *content* with step parse rates of 71.8–92.0% across
   precisions; at 8-bit, 83.9% parse against 89.3% for the 11B.

3. **Scaffolding gives an exploratory lift once format-only failures carrying the gold
   value are forgiven.** Original L0
   scores `0/10` in all eight Bielik model/precision cells at either repair setting, but
   its prompt did not state the oracle's no-tool rule. The explicit-prohibition rerun
   L0e gives the 8-bit 11B `1/10` and the 7B `0/10`: the 11B obeys and usually selects the
   wrong readings, while the 7B still calls tools. Four explicit calls lift the corrected
   rates to `9/10` and `7/10` (`p = 0.0078` and `0.016`, duplicate inputs counted).
   For the 11B the forgiven failures are pure answer typing (a bare float); for the 7B
   eight of nine also contain a rejected fifth `convert_temperature` call, so correcting
   the answer type alone would leave the 7B at `0/10`.
   L0 and L0e each have eight distinct inputs in ten slots. Removing instances e and f
   from both paired rungs gives `1/8 → 7/8` (`p = 0.03125`) and `0/8 → 5/8`
   (`p = 0.0625`). No contrast survives Holm correction over the twelve contrasts fixed
   at the analysis stage after the rerun, with or without duplicates. The order-trap
   arm separates the models at 8-bit: 11B `6/6`, 7B `0/6`; the arms also differ in tool
   identities and arithmetic placement, so this is an association with the trap.

4. **The Polish-versus-English gap is consistent with degradation or task-family
   differences.** The parent matches or beats English on long Polish chains at 8-bit,
   6-bit, 5-bit, and 3-bit; the English advantage occurs at Q4_K_M. In the compressed
   child the long Polish bucket contains the unsolved order-trap family. The language
   cells also differ in exact length and task structure, so an interface contribution
   is not isolated.

5. **Four benchmark artifacts shaped the conclusions**: rounding-hostile synthetic gold
   values shifted the apparent threshold by a full bit; strict answer typing penalized
   correct computations; a no-tool rule was enforced without being stated in the prompt;
   and priority-ordered failure labels shaped interpretation without changing pass/fail.
   Affected ladder scores are reported in strict and corrected form or, for the no-tool
   rule, with the L0e rerun. The three pilot L0 tasks inside the main suite carry the same
   unstated rule and remain as run: they cost the 11B one, one and two slots at Q8_0, Q6_K
   and Q3_K_M that end with the exact gold value.

## Repository layout

```
src/polagentbench/      benchmark engine: types, protocol parser, runner, oracle, stats
  eval/smoke.py         the oracle - authoritative pass/fail verdict
  eval/stats.py         bootstrap_ci and paired_mcnemar (stdlib only, no scipy)
tasks/adversarial/      main67 suite: 15 easy + 40 hard chains + 12 pilot ladder tasks
tasks/ladder_ext/       ladder46: 10 slots per L0/L1/L2/L3N, 6 at L3T; L0 has 8 distinct inputs
tasks/ladder_l0e/       explicit-prohibition L0 rerun tasks
tasks/ladder_l0_control/ unchanged L0 copies run as the same-session control
tasks/smoke/            5 warm-up tasks
                        (the `constraints` field of every task file is design documentation:
                        it is never passed to the model and never read by the oracle)
analysis/               analysis readers and artifact generators; see analysis/README.md
  failure_classifier.py canonical four-way failure taxonomy
  bootstrap_ci.py       95% intervals for all 18 model x quant cells
  gen_release_data.py   builds release_data/ from raw run directories
paper/                  polagentbench_paper.tex (compiles standalone, no .bib needed)
release_data/           original released data - see below
runs/L0e_2026-09/       rerun and control trajectories, matrices, manifest and analysis
tests/                  204 unit tests, no GPU and no data required
tools/                  suite validators and QA helpers
docs/                   protocol specification and provenance
  gguf_manifest.tsv     GGUF sources and hashes, with missing historical hashes disclosed
```

## Published data

`release_data/` holds the artifacts the paper promises, from the seven **clean** run
directories only — runs whose commit stamp matches the released code for `tasks/adversarial`
and `src/polagentbench/eval`. Older, superseded run directories are not published with these
clean curves; their results should not be pooled with the released data.

```
release_data/
  matrices/
    runs.csv                   73 runs: model, quant, suite, repair, pass rate, commit stamp
    per_task_main67.csv        2,457 rows - one per (run, task) on the 67-task suite
    per_task_ladder46.csv      1,288 rows - one per (run, task) on the 46-task ladder
    per_task_variance.csv        402 rows - the T=0.7 three-seed probe
    matrix_main67_wide.csv        67 rows - tasks as rows, cells as columns
  trajectories/                73 JSONL files, 4,147 trajectories, 17,221 steps
  run_logs/                    52 oracle logs (21 runs predate run-log capture)
  summaries/                   73 summary.json, each stamped with its source commit
  night_scripts/               historical harness for the 2026-07-29 session
  NIGHT_LOG.txt                that session's decision log
```

**Verdicts in the CSVs come from the oracle only.** Where a run log exists it is parsed;
otherwise verdicts are recomputed with `eval.smoke.evaluate`. Every cell is validated against
`num_passed` in its `summary.json` — the generator aborts on any mismatch.

The L0e rerun and its same-session L0 control are under `runs/L0e_2026-09/`, with
160 trajectories across 16 runs. All 80 control trajectories match the released L0 raw
model outputs, token counts and oracle verdicts; their latencies differ. GGUF provenance
is recorded in `docs/gguf_manifest.tsv`.

The `trajectory_success` column is kept as a **separate** column precisely so you can check
this yourself: that self-reported flag overstates performance in every cell, most starkly for
PLLuM at Q8_0, where it claims 66/67 against the oracle's 13/67. It is not a verdict.

## Reproducing

Environment is managed with [uv](https://docs.astral.sh/uv/); `uv.lock` pins
`llama-cpp-python` to **0.3.19**, the version that produced every run in the paper.

```bash
uv sync                      # engine, analysis and tests (no GPU needed)
uv sync --extra inference    # adds llama-cpp-python, needs a C++ toolchain
```

### Run the suite (needs a GPU and a GGUF file)

```bash
huggingface-cli download speakleash/Bielik-Minitron-7B-v3.0-Instruct-GGUF \
    minitron-Bielik-7B-v3.0-Instruct-GGUF.Q8_0.gguf --local-dir ./models

polagentbench run-suite \
    --model-path ./models/minitron-Bielik-7B-v3.0-Instruct-GGUF.Q8_0.gguf \
    --model-id bielik-minitron-7b-v3 \
    --quant Q8_0 \
    --tasks-dir tasks/adversarial \
    --n-ctx 8192 \
    --chat-format chatml \
    --prompt-language pl \
    --temperature 0.0 \
    --seeds 42 \
    --output results/my_run
```

`--repair` is off by default and stays off for baseline numbers: repair is a benchmarked
mitigation, not the baseline. Note the filename prefix is `minitron-Bielik-…`, not
`Bielik-Minitron-…`, on the publisher's side.

Greedy decoding at `--temperature 0.0` is reproducible for most but not all tasks: on the
matched-twin prompts, which are identical, raw model outputs coincide in 100 of 180 pairs
(45/60 for the 11B, 28/60 for the 7B, 27/60 for PLLuM); step and token counts coincide in
109 of 180 pairs (46/60, 32/60, 31/60). These differences are consistent with
floating-point nondeterminism in CUDA inference. Expect small differences
between re-runs; the oracle verdicts in `release_data/` are the reference.

### Re-score published trajectories (no GPU)

The oracle is the authority, and you can re-run it over the published data:

```python
import json, sys
from pathlib import Path
sys.path.insert(0, "src")
from polagentbench.io import load_all_tasks
from polagentbench.types import Trajectory
from polagentbench.eval.smoke import evaluate, SmokeStatus

tasks = {t.id: t for t in load_all_tasks(Path("tasks/adversarial"))}
path = "release_data/trajectories/v3_11b_2026-06-18__q8_no_repair.jsonl"
passed = sum(
    evaluate(tasks[(r := json.loads(line))["task_id"]],
             Trajectory.model_validate(r)).status is SmokeStatus.PASS
    for line in open(path, encoding="utf-8") if line.strip()
)
print(passed)          # 54  -> 54/67 = 0.806, the 11B Q8_0 cell of the curve
```

### Reproduce the paper's tables

```bash
uv run python -B analysis/bootstrap_ci.py     # 95% intervals, all 18 cells, seed 42
uv run python -B analysis/pllum_ceiling.py    # format-forgiveness ceilings from released data
uv run python -B analysis/ladder_typing_tolerant.py  # typing sensitivity from released data
uv run pytest -q                              # 204 tests
```

Most scripts in `analysis/` are readers. `gen_release_data.py` rebuilds `release_data/`
from historical raw run directories, and `l0e_analysis.py` rewrites the rerun matrices and
analysis report under `runs/L0e_2026-09/`. The source requirements and clean-checkout
results for every script are listed in `analysis/README.md`; some readers still require
the historical `results/` layout.

## Licensing

Code is **MIT** (`LICENSE`). The data in `release_data/` — trajectories, run logs,
summaries, outcome matrices, and the historical night-run scripts — is
**CC BY 4.0** (`release_data/LICENSE`).

## Citation

See `CITATION.cff`. The arXiv identifier is filled in once the preprint is posted.

## Status

Research code accompanying a preprint. The benchmark and the published data are stable;
the API may still change.
