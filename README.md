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
├── pyproject.toml        # Project metadata + deps (managed by uv)
├── ruff.toml             # Lint config
├── src/polagentbench/
│   ├── protocol.py       # Universal action protocol (call_tool / final_answer)
│   ├── types.py          # Task, Trajectory, FailureTag, enums
│   ├── runner.py         # Abstract runner interface (impl. in later prompt)
│   └── io.py             # YAML task loading
├── tasks/_examples/      # Dummy tasks; real benchmark tasks added later
├── tests/                # Pytest suite
└── docs/protocol.md      # Spec of the universal action protocol
```

## Install

We use [uv](https://github.com/astral-sh/uv) for environment management.

```bash
uv sync
```

This installs runtime + dev dependencies into `.venv/`.

## Run tests

```bash
uv run pytest
```

## Lint

```bash
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

## What's in this commit

This is the initial scaffolding. It contains:

- The universal action protocol (`call_tool`, `final_answer`) with a tolerant
  parser that handles markdown-wrapped JSON.
- Core pydantic types: `Task`, `Trajectory`, `TrajectoryStep`, plus enums for
  task category, interface variant, and failure tags.
- An abstract `ModelRunner` interface (concrete `LlamaCppRunner`
  implementation comes in a later prompt).
- A YAML task loader and one dummy task to validate the schema end-to-end.
- Unit tests covering protocol parsing and task loading.

What's deliberately **not** here yet: actual model inference, real environments
(CRM / invoices / calendar), evaluators, mitigations, automatic failure tagging,
or the actual benchmark tasks. Those land in subsequent prompts.

## License

MIT.
