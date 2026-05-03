"""All 10 adversarial task YAMLs must load and validate cleanly.

A trivial check, but it catches authoring errors (typos in oracle keys,
unknown FailureTag names, malformed YAML) at suite-collection time rather
than mid-run on the GPU box.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from polagentbench.io import load_all_tasks, load_task
from polagentbench.types import InterfaceVariant

REPO_ROOT = Path(__file__).resolve().parent.parent
ADV_DIR = REPO_ROOT / "tasks" / "adversarial"


def test_all_ten_adversarial_tasks_load():
    tasks = load_all_tasks(ADV_DIR)
    ids = sorted(t.id for t in tasks)
    assert ids == [f"adv_{n:03d}" for n in range(1, 11)]


def test_all_adversarial_tasks_are_pl_en():
    for t in load_all_tasks(ADV_DIR):
        assert t.language_variant is InterfaceVariant.PL_EN


def test_all_adversarial_tasks_use_weather_env():
    for t in load_all_tasks(ADV_DIR):
        assert t.environment == "weather"


def test_all_adversarial_tasks_have_actionable_oracle():
    """Every task must reference at least one recognised oracle key."""
    from polagentbench.eval.smoke import _CHECKS  # type: ignore[attr-defined]

    for t in load_all_tasks(ADV_DIR):
        keys = [k for k in t.expected_final_state if k in _CHECKS]
        assert keys, f"{t.id} has no recognised oracle keys"


@pytest.mark.parametrize("task_id", ["adv_003", "adv_004"])
def test_strict_match_tasks_set_strict_match_flag(task_id: str):
    task = load_task(ADV_DIR / f"{task_id}.yaml")
    assert task.strict_match is True


@pytest.mark.parametrize("task_id", ["adv_006", "adv_008"])
def test_hardcoded_state_tasks_pin_a_city(task_id: str):
    task = load_task(ADV_DIR / f"{task_id}.yaml")
    assert task.hardcoded_state is not None
    assert "cities" in task.hardcoded_state


def test_adv_010_disallows_tool_calls():
    task = load_task(ADV_DIR / "adv_010.yaml")
    assert task.expected_final_state.get("no_tool_calls") is True
