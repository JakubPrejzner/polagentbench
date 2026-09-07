"""Resolve results-style run directories against the released data layout."""

from pathlib import Path
from typing import NamedTuple


class RunPaths(NamedTuple):
    trajectories: Path
    summary: Path
    run_log: Path | None


def resolve_run_paths(run_directory: str | Path) -> RunPaths:
    """Prefer an existing ``results/`` run, otherwise use ``release_data/``."""
    run_directory = Path(run_directory)
    if run_directory.is_dir():
        run_log = run_directory / "run.log"
        return RunPaths(
            run_directory / "trajectories.jsonl",
            run_directory / "summary.json",
            run_log if run_log.is_file() else None,
        )

    if run_directory.parent.parent.name != "results":
        raise ValueError(f"expected results/<run_dir>/<run>, got {run_directory}")

    run_id = f"{run_directory.parent.name}__{run_directory.name}"
    run_log = Path("release_data/run_logs") / f"{run_id}.log"
    return RunPaths(
        Path("release_data/trajectories") / f"{run_id}.jsonl",
        Path("release_data/summaries") / f"{run_id}.json",
        run_log if run_log.is_file() else None,
    )
