"""Integration-style: every YAML under tasks/ must load without error."""

from __future__ import annotations

from pathlib import Path

from polagentbench.io import load_all_tasks

REPO_ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = REPO_ROOT / "tasks"


def test_all_tasks_load():
    tasks = load_all_tasks(TASKS_DIR)
    assert len(tasks) >= 1, "expected at least the dummy task to be present"
    ids = [t.id for t in tasks]
    assert len(ids) == len(set(ids)), f"duplicate task ids: {ids}"


def test_dummy_task_present():
    tasks = load_all_tasks(TASKS_DIR)
    assert any(t.id == "dummy_001" for t in tasks)
