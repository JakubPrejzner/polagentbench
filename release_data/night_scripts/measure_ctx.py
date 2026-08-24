"""BRAMKA B — peak prompt-token measurement for the PLLuM curve.

Read-only instrumentation: wraps LlamaCppRunner._complete_chat to record the
prompt_tokens llama.cpp reports for every step, then reports the PEAK (last
step of the longest chain).  Nothing under src/ or tasks/ is touched.

usage: measure_ctx.py <model_path> <chat_format> <n_ctx> <task.yaml> [task.yaml ...]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from polagentbench.cli import _build_environments
from polagentbench.inference.llama_cpp_runner import LlamaCppRunner
from polagentbench.io import load_task

model_path, chat_format, n_ctx = sys.argv[1], sys.argv[2], int(sys.argv[3])
task_paths = sys.argv[4:]

runner = LlamaCppRunner(
    model_path=model_path,
    model_id="llama-pllum-8b",
    quant_label="Q8_0",
    environments=_build_environments(),
    n_ctx=n_ctx,
    chat_format=chat_format,
    prompt_language="pl",
    temperature=0.0,
)

seen: list[tuple[str, int, int]] = []  # (task_id, step_idx, prompt_tokens)
current = {"id": "?"}
orig = runner._complete_chat


def probe(messages, seed):
    text, latency, usage = orig(messages, seed)
    pt = int((usage or {}).get("prompt_tokens", 0) or 0)
    seen.append((current["id"], len([m for m in messages]), pt))
    return text, latency, usage


runner._complete_chat = probe

for tp in task_paths:
    task = load_task(Path(tp))
    current["id"] = task.id
    traj = runner.run_task(task, seed=42)
    rows = [r for r in seen if r[0] == task.id]
    peak = max((r[2] for r in rows), default=0)
    print(
        f"{task.id:28s} max_steps={task.max_steps:2d} steps_taken={len(rows):2d} "
        f"peak_prompt_tokens={peak:5d} total_tokens={traj.total_tokens}"
    )

overall = max((r[2] for r in seen), default=0)
print(f"\nPEAK_PROMPT_TOKENS_OVERALL={overall}  (n_ctx={n_ctx})")
