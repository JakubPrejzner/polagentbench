# PolAgentBench

A Polish-first benchmark for measuring what GGUF quantization does to **agentic tool use** —
calling the right tools in the right order and computing correct answers from their outputs —
in a realistic non-English setting: Polish prompts against English tool schemas.

Three models, six precisions each (Q8_0 down to Q2_K), 113 deterministic tasks.
This repository holds the benchmark, every trajectory we collected, the per-task outcome
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

The Bielik pair isolates **model compression** with architecture, corpus, and tokenizer held
fixed. PLLuM adds the **pretraining-family** axis at comparable scale while staying a
Polish-focused model, so the family axis is not confounded with the interface language.

## Five results

1. **The collapse threshold replicates across all three models.** Every model falls off a
   cliff between 3-bit and 2-bit: 11B `0.716 → 0.045`, 7B `0.463 → 0.149`, PLLuM
   `0.224 → 0.015`. Paired exact McNemar gives `p < 0.0001` for both Bieliks and
   `p = 0.0001` for PLLuM — across a fourfold spread in absolute capability, across
   compression by pruning plus distillation, and across a change of pretraining family.

2. **Failure modes do not replicate. Three models, three signatures.** The 7B hangs
   (median failing trajectory 26,833 tokens), the 11B disintegrates (1,506 tokens, often a
   single step), and PLLuM fails on *content* while speaking the protocol fluently —
   83.9% of its steps parse, against 89.3% for the 11B, yet its content-to-format failure
   ratio is inverted relative to Bielik.

3. **Scaffolding helps rather than hurts, once an answer-typing artifact is corrected.**
   Bare arithmetic (rung L0, no tool calls permitted) is `0/10` in all eight Bielik ladder
   runs. Routing the identical computation through four explicit calls lifts the 11B to
   `9/10` (`p = 0.004`) and the 7B to `7/10` (`p = 0.016`) at 8-bit. The order-trap arm
   separates the models cleanly: 11B `6/6`, 7B `0/6`.

4. **The Polish-versus-English gap is a signature of degradation, not a property of the
   interface.** In the parent model Polish matches or beats English on long chains at every
   healthy precision and the English advantage appears only at the anomalous Q4_K_M dip; in
   the compressed child the gap is a proxy for one unsolved task family, the 4-tool
   order-trap chains.

5. **Three benchmark artifacts materially shaped the conclusions, and are documented rather
   than hidden**: a rounding mine in synthetic gold values that had shifted the apparent
   threshold by a full bit; a priority-ordered failure taxonomy whose labels are
   indeterminate in specific cells; and strict answer typing that penalized correct
   computations. Affected results are reported in both strict and corrected form.

## Repository layout

```
src/polagentbench/      benchmark engine: types, protocol parser, runner, oracle, stats
  eval/smoke.py         the oracle - authoritative pass/fail verdict
  eval/stats.py         bootstrap_ci and paired_mcnemar (stdlib only, no scipy)
tasks/adversarial/      main67 suite: 15 easy (adv_*) + 52 hard chains
tasks/ladder_ext/       ladder46 suite: L0/L1/L2/L3N at n=10, L3T at n=6
tasks/smoke/            5 warm-up tasks
analysis/               read-only scripts reproducing every table in the paper
  failure_classifier.py canonical four-way failure taxonomy
  bootstrap_ci.py       95% intervals for all 18 model x quant cells
  gen_release_data.py   builds release_data/ from raw run directories
paper/                  polagentbench_paper.tex (compiles standalone, no .bib needed)
release_data/           all published data - see below
tests/                  204 unit tests, no GPU and no data required
tools/                  suite validators and QA helpers
docs/                   protocol specification
```

## Published data

`release_data/` holds the artifacts the paper promises, from the seven **clean** run
directories only — runs whose commit stamp matches the released code for `tasks/adversarial`
and `src/polagentbench/eval`. Four older, superseded run directories are deliberately not
published; their task definitions and oracle differ from this code, so numbers from them are
not comparable.

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
matched-twin prompts, which are identical, the published trajectories coincide in 109 of
180 pairs across the three models (46/60 for the 11B, 32/60 for the 7B, 31/60 for PLLuM),
consistent with floating-point nondeterminism in CUDA inference. Expect small differences
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
uv run python analysis/bootstrap_ci.py        # 95% intervals, all 18 cells, seed 42
uv run python analysis/gen_release_data.py    # rebuilds release_data/ from raw runs
uv run pytest -q                              # 204 tests
```

Every script in `analysis/` is read-only and names its data sources in its docstring.
Scripts that read raw run directories need those directories present; the published
`release_data/` is a redistribution of the same content in a flatter layout.

## Licensing

Code is **MIT** (`LICENSE`). The data in `release_data/` — trajectories, run logs,
summaries, outcome matrices, and the historical night-run scripts — is
**CC BY 4.0** (`release_data/LICENSE`).

## Citation

See `CITATION.cff`. The arXiv identifier is filled in once the preprint is posted.

## Status

Research code accompanying a preprint. The benchmark and the published data are stable;
the API may still change.
