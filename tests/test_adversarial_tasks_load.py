"""All 67 adversarial task YAMLs must load and validate cleanly.

A trivial check, but it catches authoring errors (typos in oracle keys,
unknown FailureTag names, malformed YAML) at suite-collection time rather
than mid-run on the GPU box.

In prompt 03.5 the original adv_004 and adv_009 were each split into two
cleaner tasks (4a/4b, 9a/9b) and three mid-difficulty tasks (011-013) were
added to widen the gradient between ceiling-bound and floor-bound tasks.
Suite consolidation 2026-06-10: hard tier = 30 original chains + 12
arithmetic-isolation ladder tasks (v3_arith_L{0..3}_{a,b,c}) + 10 B2-1
length/language chains (v3_chain_012-016, v3_chain_en_010-014) = 52;
plus the 15 easy adv_* tasks -> 67 total.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from polagentbench.io import load_all_tasks, load_task
from polagentbench.types import InterfaceVariant

REPO_ROOT = Path(__file__).resolve().parent.parent
ADV_DIR = REPO_ROOT / "tasks" / "adversarial"

EXPECTED_TASK_IDS = sorted(
    [
        "adv_001",
        "adv_002",
        "adv_003",
        "adv_004a",
        "adv_004b",
        "adv_005",
        "adv_006",
        "adv_007",
        "adv_008",
        "adv_009a",
        "adv_009b",
        "adv_010",
        "adv_011",
        "adv_012",
        "adv_013",
        "v3_arith_L0_a",
        "v3_arith_L0_b",
        "v3_arith_L0_c",
        "v3_arith_L1_a",
        "v3_arith_L1_b",
        "v3_arith_L1_c",
        "v3_arith_L2_a",
        "v3_arith_L2_b",
        "v3_arith_L2_c",
        "v3_arith_L3_a",
        "v3_arith_L3_b",
        "v3_arith_L3_c",
        "v3_chain_001",
        "v3_chain_001_arith",
        "v3_chain_002",
        "v3_chain_003",
        "v3_chain_en_001",
        "v3_chain_en_001_arith",
        "v3_chain_en_002",
        "v3_chain_004",
        "v3_chain_004_arith",
        "v3_chain_005",
        "v3_chain_005_arith",
        "v3_chain_006",
        "v3_chain_006_arith",
        "v3_chain_007",
        "v3_chain_007_arith",
        "v3_chain_008",
        "v3_chain_009",
        "v3_chain_010",
        "v3_chain_010_arith",
        "v3_chain_011",
        "v3_chain_012",
        "v3_chain_013",
        "v3_chain_014",
        "v3_chain_015",
        "v3_chain_016",
        "v3_chain_en_003",
        "v3_chain_en_003_arith",
        "v3_chain_en_004",
        "v3_chain_en_004_arith",
        "v3_chain_en_005",
        "v3_chain_en_005_arith",
        "v3_chain_en_006",
        "v3_chain_en_007",
        "v3_chain_en_008",
        "v3_chain_en_009",
        "v3_chain_en_010",
        "v3_chain_en_011",
        "v3_chain_en_012",
        "v3_chain_en_013",
        "v3_chain_en_014",
    ]
)


def test_all_adversarial_tasks_load():
    tasks = load_all_tasks(ADV_DIR)
    ids = sorted(t.id for t in tasks)
    assert ids == EXPECTED_TASK_IDS


EN_EN_TASK_IDS = {
    "v3_chain_en_001",
    "v3_chain_en_001_arith",
    "v3_chain_en_002",
    "v3_chain_en_003",
    "v3_chain_en_003_arith",
    "v3_chain_en_004",
    "v3_chain_en_004_arith",
    "v3_chain_en_005",
    "v3_chain_en_005_arith",
    "v3_chain_en_006",
    "v3_chain_en_007",
    "v3_chain_en_008",
    "v3_chain_en_009",
    "v3_chain_en_010",
    "v3_chain_en_011",
    "v3_chain_en_012",
    "v3_chain_en_013",
    "v3_chain_en_014",
}


def test_adversarial_task_language_variants():
    """adv_* and the PL v3 chains are PL_EN; v3_chain_en_* chains are EN_EN."""
    for t in load_all_tasks(ADV_DIR):
        expected = (
            InterfaceVariant.EN_EN if t.id in EN_EN_TASK_IDS else InterfaceVariant.PL_EN
        )
        assert t.language_variant is expected, t.id


def test_all_adversarial_tasks_use_weather_env():
    for t in load_all_tasks(ADV_DIR):
        assert t.environment == "weather"


def test_all_adversarial_tasks_have_actionable_oracle():
    """Every task must reference at least one recognised oracle key."""
    from polagentbench.eval.smoke import _CHECKS  # type: ignore[attr-defined]

    for t in load_all_tasks(ADV_DIR):
        keys = [k for k in t.expected_final_state if k in _CHECKS]
        assert keys, f"{t.id} has no recognised oracle keys"


@pytest.mark.parametrize("task_id", ["adv_003", "adv_004a", "adv_004b"])
def test_strict_match_tasks_set_strict_match_flag(task_id: str):
    task = load_task(ADV_DIR / f"{task_id}.yaml")
    assert task.strict_match is True


@pytest.mark.parametrize("task_id", ["adv_006", "adv_008", "adv_012"])
def test_hardcoded_state_tasks_pin_a_city(task_id: str):
    task = load_task(ADV_DIR / f"{task_id}.yaml")
    assert task.hardcoded_state is not None
    assert "cities" in task.hardcoded_state


def test_adv_010_disallows_tool_calls():
    task = load_task(ADV_DIR / "adv_010.yaml")
    assert task.expected_final_state.get("no_tool_calls") is True


def test_adv_004b_uses_final_answer_is_string_oracle():
    task = load_task(ADV_DIR / "adv_004b.yaml")
    assert task.expected_final_state.get("final_answer_is_string") is True


def test_adv_013_uses_strict_order_oracle():
    task = load_task(ADV_DIR / "adv_013.yaml")
    assert "tools_called_in_order_strict" in task.expected_final_state


def test_adv_012_forbids_alert_via_max_tool_calls_zero():
    task = load_task(ADV_DIR / "adv_012.yaml")
    max_calls = task.expected_final_state.get("max_tool_calls", {})
    assert max_calls.get("send_weather_alert") == 0
