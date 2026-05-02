# PolAgentBench

> **Status:** WIP — research code, not production. APIs and task definitions will change.

PolAgentBench is a Polish-first agent evaluation benchmark for studying how
quantization interacts with **language-interface mismatch** in tool-using LLMs:
specifically, what happens when a model is asked Polish-language questions while
its tools are described with English schemas (the typical real-world setup).

The benchmark is designed to expose failure modes that are invisible to
English-only evaluations — schema fracture, language leakage in tool arguments,
inflection / diacritic corruption of identifiers, and recovery collapse — and to
measure how aggressively these emerge as quantization is pushed from BF16 down
to Q4_K_M and Q2_K.

## Project goals (full picture, not all implemented yet)

- **Models under test:** Bielik-Minitron-7B-v3.0-Instruct, Bielik-11B-v3.0-Instruct,
  Qwen2.5-7B-Instruct.
- **Quantization levels:** BF16 / Q8 reference, Q4_K_M, Q2_K (failure boundary).
- **Inference stack:** [llama.cpp](https://github.com/ggerganov/llama.cpp) via
  `llama-cpp-python`, GGUF format only.
- **Task categories (4):** tool selection, stateful multi-step, constraint
  following, error recovery.
- **Interface variants (3):** EN+EN schema, PL+EN schema, PL+EN with PL
  descriptions.
- **Universal action protocol** — all models output the same JSON action shape;
  we deliberately do *not* use any vendor's native tool-calling so that the
  comparison is apples-to-apples across model families.

## Repository layout

```
polagentbench/
├── pyproject.toml             # Project metadata + deps (managed by uv)
├── ruff.toml                  # Lint config
├── src/polagentbench/
│   ├── cli.py                 # `polagentbench run` / `run-suite`
│   ├── protocol.py            # Universal action protocol parser
│   ├── types.py               # Task, Trajectory, FailureTag, enums
│   ├── runner.py              # Abstract ModelRunner interface
│   ├── io.py                  # YAML task loading
│   ├── environments/
│   │   ├── base.py            # Environment ABC
│   │   └── weather.py         # Weather env (5 tools)
│   ├── inference/
│   │   ├── prompts.py         # System-prompt builder (PL / EN)
│   │   └── llama_cpp_runner.py # Agent loop + LlamaCppRunner
│   └── eval/
│       └── smoke.py           # Permissive smoke evaluator
├── tasks/
│   ├── _examples/             # Dummy task (loader smoke test)
│   └── smoke/                 # 5 PL-prompt + EN-schema weather tasks
├── tests/                     # Pytest suite
└── docs/protocol.md           # Universal action protocol spec
```

## Install

We use [uv](https://github.com/astral-sh/uv) for environment management.

For development (no model inference):

```bash
uv sync --extra dev
```

To run the smoke suite end-to-end, also install the optional `inference`
extra (pulls in `llama-cpp-python` — needs a C++ toolchain on Linux/macOS or
prebuilt CUDA wheels via `pip install llama-cpp-python --extra-index-url
https://abetlen.github.io/llama-cpp-python/whl/cu124` on a 4090):

```bash
uv sync --extra dev --extra inference
```

## Run tests

```bash
uv run pytest
```

## Lint

```bash
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

## Smoke suite — running end-to-end

The smoke suite answers one question:

> Does Bielik-Minitron-7B-v3.0-Instruct (Q8_0 GGUF) successfully call the
> right tool with correct arguments on simple PL-prompt + EN-schema tasks?

Five Polish tasks (`tasks/smoke/`) all target the `weather` environment.
Pass-rate ≥ 60% on Q8 means the project is feasible and we proceed to the
full benchmark; below that, the strategy needs a rethink.

### 1. Download the model

Get a GGUF build of Bielik-Minitron-7B-v3.0-Instruct from Hugging Face:

```bash
huggingface-cli download speakleash/Bielik-Minitron-7B-v3.0-Instruct-GGUF \
    Bielik-Minitron-7B-v3.0-Instruct.Q8_0.gguf \
    --local-dir ./models
```

(Exact GGUF filename / repo may vary across uploaders; pick the one whose
chat template is ChatML.)

### 2. Run the smoke suite

```bash
uv run polagentbench run-suite \
    --model-path ./models/Bielik-Minitron-7B-v3.0-Instruct.Q8_0.gguf \
    --model-id bielik-minitron-7b-v3 \
    --quant Q8_0 \
    --tasks-dir tasks/smoke/ \
    --seeds 42 \
    --output results/smoke_run_001/
```

Expected wall-clock on an RTX 4090: **under 5 minutes** for 5 tasks × 1 seed
(typical trajectory is 2–4 model turns of <512 generated tokens each).

Outputs:

```
results/smoke_run_001/
├── trajectories.jsonl   # one Trajectory per line
└── summary.json         # aggregate pass rate + failure-tag histogram
```

The console prints a per-task report at the end:

```
Smoke test results - bielik-minitron-7b-v3 / Q8_0 / seed=42
============================================================
weather_smoke_001  ✓  get_weather(city='Kraków') -> final_answer
weather_smoke_002  ✗  get_weather(city='Lodz') -> final_answer - insufficient_tool_calls
weather_smoke_003  ✗  send_weather_alert(severity='wysoka', ...) -> ... - language_leakage
weather_smoke_004  ✓  get_weather(...) -> convert_temperature(...) -> final_answer
weather_smoke_005  ✓  get_weather(city='Atlantis') -> final_answer
============================================================
Success: 3/5 (60%)
Failure tags: {insufficient_tool_calls: 1, language_leakage: 1, wrong_tool_args: 1}
```

## What's in this state of the repo

- Universal action protocol with a tolerant parser.
- Core pydantic types (`Task`, `Trajectory`, `TrajectoryStep`) and enums.
- Abstract `ModelRunner` plus a concrete `LlamaCppRunner` that drives a
  GGUF model via `llama-cpp-python` and a testable module-level `agent_loop`.
- A `weather` environment with 5 tools, diacritic normalisation, and an
  `alerts_sent` log.
- PL/EN system-prompt builder.
- Permissive smoke evaluator and CLI (`polagentbench run` / `run-suite`).
- 5 PL-prompt + EN-schema smoke tasks targeting the failure modes the
  full benchmark will measure.

What's deliberately **not** here yet: stateful environments (CRM, invoices,
calendar), constraint validators, recovery scenarios, mitigations, multiple
language variants beyond `PL_EN`, automatic `FailureTag` inference, the
HuggingFace dataset export, and the actual benchmark tasks.

## License

MIT.
