"""YAML loading helpers for benchmark tasks.

Tasks are stored as YAML so they're easy to author and review by hand. We
parse with ``yaml.safe_load`` (no arbitrary Python constructors) and validate
through the pydantic :class:`Task` model, so any structural error surfaces at
load time rather than mid-run.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from .types import Task

__all__ = ["load_all_tasks", "load_task"]


def load_task(path: Path) -> Task:
    """Load and validate a single task YAML file.

    Args:
        path: Path to a ``.yaml`` (or ``.yml``) file describing one task.

    Returns:
        A validated :class:`Task` instance.

    Raises:
        FileNotFoundError: if ``path`` does not exist.
        ValueError: if the YAML cannot be parsed or fails Task validation.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Task file not found: {path}")

    with path.open("r", encoding="utf-8") as fh:
        try:
            data = yaml.safe_load(fh)
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid YAML in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Task file {path} must contain a YAML mapping at the top level.")

    return Task.model_validate(data)


def load_all_tasks(directory: Path) -> list[Task]:
    """Recursively load every ``.yaml`` / ``.yml`` task under ``directory``.

    Tasks are returned in sorted-by-path order for deterministic iteration.

    Args:
        directory: Root directory to scan.

    Returns:
        List of validated :class:`Task` instances.

    Raises:
        FileNotFoundError: if ``directory`` does not exist or is not a dir.
        ValueError: if any individual task fails to load.
    """
    directory = Path(directory)
    if not directory.is_dir():
        raise FileNotFoundError(f"Not a directory: {directory}")

    paths = sorted({*directory.rglob("*.yaml"), *directory.rglob("*.yml")})
    return [load_task(p) for p in paths]
