"""Command-line entry point for PolAgentBench.

Two subcommands:

* ``polagentbench run`` — run a single task at a single seed.
* ``polagentbench run-suite`` — run a directory of tasks across one or
  more seeds, write per-trajectory JSONL plus a ``summary.json``, and print
  a human-readable smoke report.

The CLI is the only place that knows how to wire concrete environments to
the runner. New environments register themselves in ``_ENVIRONMENT_FACTORIES``
below.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from .environments.base import Environment
from .environments.weather import WeatherEnvironment
from .eval.smoke import (
    SmokeResult,
    aggregate_grid_summary,
    aggregate_summary,
    evaluate,
    format_console_report,
    format_grid_report,
)
from .io import load_all_tasks, load_task
from .runner import ModelRunner
from .types import Task, Trajectory

__all__ = ["build_parser", "main"]


# ---------------------------------------------------------------------------
# Environment registry
# ---------------------------------------------------------------------------

_ENVIRONMENT_FACTORIES: dict[str, Callable[[], Environment]] = {
    "weather": WeatherEnvironment,
}


def _build_environments() -> dict[str, Environment]:
    return {name: factory() for name, factory in _ENVIRONMENT_FACTORIES.items()}


# ---------------------------------------------------------------------------
# Argparse
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="polagentbench",
        description="Polish-first agent evaluation benchmark.",
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="<command>")

    # Shared model arguments factored into a helper.
    def _add_model_args(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--model-path", type=Path, required=True, help="Path to the GGUF model file."
        )
        p.add_argument("--model-id", required=True, help="Stable identifier for the model.")
        p.add_argument("--quant", required=True, help="Quantization label (e.g. Q8_0, Q4_K_M).")
        p.add_argument("--n-ctx", type=int, default=8192, help="Context window in tokens.")
        p.add_argument(
            "--n-gpu-layers",
            type=int,
            default=-1,
            help="Number of layers to offload to GPU. -1 = all.",
        )
        p.add_argument(
            "--prompt-language",
            choices=["pl", "en"],
            default="pl",
            help="System-prompt language. Smoke runs use Polish.",
        )
        p.add_argument(
            "--chat-format", default="chatml", help="llama.cpp chat template (default: chatml)."
        )
        p.add_argument("--max-tokens", type=int, default=512)
        p.add_argument("--temperature", type=float, default=0.0)
        p.add_argument("--top-p", type=float, default=1.0)
        p.add_argument(
            "--repair",
            action="store_true",
            help=(
                "Apply attempt_repair to each model output before parsing. "
                "Default OFF — repair is a benchmarked mitigation, not the baseline."
            ),
        )
        p.add_argument("--verbose", action="store_true")

    # `run`
    run_p = sub.add_parser("run", help="Run a single task at one seed.")
    _add_model_args(run_p)
    run_p.add_argument("--task", type=Path, required=True, help="Path to a task YAML.")
    run_p.add_argument("--seed", type=int, default=42)
    run_p.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output directory; trajectories.jsonl and summary.json are written here.",
    )

    # `run-suite`
    suite_p = sub.add_parser(
        "run-suite", help="Run all tasks in a directory across one or more seeds."
    )
    _add_model_args(suite_p)
    suite_p.add_argument("--tasks-dir", type=Path, required=True, help="Directory of task YAMLs.")
    suite_p.add_argument(
        "--seeds",
        default="42",
        help="Comma-separated seed list, e.g. '42,43,44'.",
    )
    suite_p.add_argument(
        "--temperatures",
        default=None,
        help=(
            "Comma-separated temperature list, e.g. '0.0,0.3,0.7'. When set, "
            "overrides --temperature and runs the full task x temp x seed grid."
        ),
    )
    suite_p.add_argument("--output", type=Path, required=True, help="Output directory.")

    return parser


def _parse_seeds(seeds_str: str) -> list[int]:
    parts = [s.strip() for s in seeds_str.split(",") if s.strip()]
    if not parts:
        raise argparse.ArgumentTypeError("at least one seed is required")
    try:
        return [int(s) for s in parts]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid seed in {seeds_str!r}: {exc}") from exc


def _parse_temperatures(temps_str: str) -> list[float]:
    parts = [s.strip() for s in temps_str.split(",") if s.strip()]
    if not parts:
        raise argparse.ArgumentTypeError("at least one temperature is required")
    try:
        return [float(s) for s in parts]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"invalid temperature in {temps_str!r}: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Runner construction (kept indirect so tests can override)
# ---------------------------------------------------------------------------


RunnerFactory = Callable[[argparse.Namespace, dict[str, Environment]], ModelRunner]


def _default_runner_factory(
    args: argparse.Namespace, environments: dict[str, Environment]
) -> ModelRunner:
    from .inference.llama_cpp_runner import LlamaCppRunner

    return LlamaCppRunner(
        model_path=args.model_path,
        model_id=args.model_id,
        quant_label=args.quant,
        environments=environments,
        n_ctx=args.n_ctx,
        n_gpu_layers=args.n_gpu_layers,
        verbose=args.verbose,
        prompt_language=args.prompt_language,
        chat_format=args.chat_format,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        top_p=args.top_p,
        repair=args.repair,
    )


# ---------------------------------------------------------------------------
# Suite execution
# ---------------------------------------------------------------------------


def _run_suite(
    tasks: list[Task],
    seeds: Sequence[int],
    runner: ModelRunner,
    output_dir: Path,
    *,
    model_id: str,
    quant_label: str,
    repair: bool,
    seed_for_console: int | None = None,
) -> tuple[list[Trajectory], list[SmokeResult]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    trajectories_path = output_dir / "trajectories.jsonl"
    summary_path = output_dir / "summary.json"

    trajectories: list[Trajectory] = []
    results: list[SmokeResult] = []

    with trajectories_path.open("w", encoding="utf-8") as fh:
        for task in tasks:
            for seed in seeds:
                trajectory = runner.run_task(task, seed)
                fh.write(trajectory.model_dump_json() + "\n")
                fh.flush()
                trajectories.append(trajectory)
                results.append(evaluate(task, trajectory))

    summary = aggregate_summary(
        results,
        trajectories,
        model_id=model_id,
        quant_label=quant_label,
        repair=repair,
    )
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    report = format_console_report(
        results, model_id=model_id, quant_label=quant_label, seed=seed_for_console
    )
    print(report)
    return trajectories, results


# ---------------------------------------------------------------------------
# Subcommand handlers
# ---------------------------------------------------------------------------


def _cmd_run(args: argparse.Namespace, runner_factory: RunnerFactory) -> int:
    task = load_task(args.task)
    environments = _build_environments()
    runner = runner_factory(args, environments)
    _run_suite(
        tasks=[task],
        seeds=[args.seed],
        runner=runner,
        output_dir=args.output,
        model_id=args.model_id,
        quant_label=args.quant,
        repair=args.repair,
        seed_for_console=args.seed,
    )
    return 0


def _cmd_run_suite(args: argparse.Namespace, runner_factory: RunnerFactory) -> int:
    tasks = load_all_tasks(args.tasks_dir)
    if not tasks:
        print(f"no tasks found under {args.tasks_dir}", file=sys.stderr)
        return 2
    seeds = _parse_seeds(args.seeds)

    # --temperatures overrides --temperature when supplied. With only the
    # singular flag, behaviour is unchanged from prompt 02 (single-temp run).
    if args.temperatures is not None:
        temperatures = _parse_temperatures(args.temperatures)
    else:
        temperatures = [float(args.temperature)]

    environments = _build_environments()
    runner = runner_factory(args, environments)

    if len(temperatures) == 1:
        runner.temperature = temperatures[0]  # type: ignore[attr-defined]
        _run_suite(
            tasks=tasks,
            seeds=seeds,
            runner=runner,
            output_dir=args.output,
            model_id=args.model_id,
            quant_label=args.quant,
            repair=args.repair,
            seed_for_console=seeds[0] if len(seeds) == 1 else None,
        )
        return 0

    _run_grid(
        tasks=tasks,
        temperatures=temperatures,
        seeds=seeds,
        runner=runner,
        output_dir=args.output,
        model_id=args.model_id,
        quant_label=args.quant,
        repair=args.repair,
    )
    return 0


def _run_grid(
    tasks: list[Task],
    temperatures: Sequence[float],
    seeds: Sequence[int],
    runner: ModelRunner,
    output_dir: Path,
    *,
    model_id: str,
    quant_label: str,
    repair: bool,
) -> None:
    """Drive the (temperature, seed, task) cartesian product of trajectories.

    Mutates ``runner.temperature`` between conditions so a single loaded
    model serves the whole grid — re-loading the GGUF per temperature
    would dominate wall time.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    trajectories_path = output_dir / "trajectories.jsonl"
    summary_path = output_dir / "summary.json"

    cells: list[dict[str, Any]] = []
    task_ids = [t.id for t in tasks]

    with trajectories_path.open("w", encoding="utf-8") as fh:
        for temperature in temperatures:
            runner.temperature = float(temperature)  # type: ignore[attr-defined]
            for seed in seeds:
                for task in tasks:
                    trajectory = runner.run_task(task, seed)
                    fh.write(trajectory.model_dump_json() + "\n")
                    fh.flush()
                    result = evaluate(task, trajectory)
                    cells.append(
                        {
                            "temperature": float(temperature),
                            "seed": int(seed),
                            "task_id": task.id,
                            "passed": result.status.value == "PASS",
                            "status": result.status.value,
                            "failure_tags": list(dict.fromkeys(result.failure_tags)),
                            "trajectory_summary": result.trajectory_summary,
                            "latency_ms": float(trajectory.total_latency_ms),
                            "repair_applied_steps": sum(
                                1 for s in trajectory.steps if s.repair_applied
                            ),
                        }
                    )

    summary = aggregate_grid_summary(
        cells,
        model_id=model_id,
        quant_label=quant_label,
        repair=repair,
        temperatures=list(temperatures),
        seeds=list(seeds),
        task_ids=task_ids,
    )
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(format_grid_report(summary))


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------


def main(
    argv: Sequence[str] | None = None,
    *,
    runner_factory: RunnerFactory | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    factory = runner_factory or _default_runner_factory

    if args.command == "run":
        return _cmd_run(args, factory)
    if args.command == "run-suite":
        return _cmd_run_suite(args, factory)
    parser.error(f"unknown command: {args.command}")
    return 2  # pragma: no cover


if __name__ == "__main__":
    sys.exit(main())
