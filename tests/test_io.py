"""Tests for YAML task loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from polagentbench.io import load_task
from polagentbench.types import InterfaceVariant, TaskCategory

REPO_ROOT = Path(__file__).resolve().parent.parent
DUMMY_TASK_PATH = REPO_ROOT / "tasks" / "_examples" / "dummy_001.yaml"


def test_dummy_task_loads_successfully():
    task = load_task(DUMMY_TASK_PATH)
    assert task.id == "dummy_001"
    assert task.category is TaskCategory.TOOL_SELECTION
    assert task.environment == "weather"
    assert task.language_variant is InterfaceVariant.PL_EN
    assert task.prompt == "Sprawdź pogodę w Krakowie."
    assert task.max_steps == 3
    assert task.constraints == ["Use only one tool call."]


def test_load_task_sets_source_path():
    task = load_task(DUMMY_TASK_PATH)
    assert task.source_path is not None
    assert task.source_path == DUMMY_TASK_PATH.resolve()


def test_load_task_rejects_yaml_setting_source_path(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "id: bad\n"
        "category: TOOL_SELECTION\n"
        "environment: weather\n"
        "language_variant: EN_EN\n"
        "prompt: hello\n"
        "available_tools: []\n"
        "initial_state_path: states/empty.json\n"
        "expected_final_state: {}\n"
        "source_path: /tmp/forged.yaml\n",
        encoding="utf-8",
    )
    import pytest

    with pytest.raises(ValueError):
        load_task(bad)


def test_dummy_task_tool_schemas_preserved():
    task = load_task(DUMMY_TASK_PATH)
    assert len(task.available_tools) == 2
    names = [t["name"] for t in task.available_tools]
    assert names == ["get_weather", "send_email"]
    weather_schema = task.available_tools[0]
    assert weather_schema["parameters"]["required"] == ["city"]


def test_dummy_task_initial_state_path_resolves():
    task = load_task(DUMMY_TASK_PATH)
    assert str(task.initial_state_path).replace("\\", "/") == "states/empty.json"
    resolved = (DUMMY_TASK_PATH.parent / task.initial_state_path).resolve()
    assert resolved.exists()


def test_load_task_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_task(REPO_ROOT / "tasks" / "_examples" / "does_not_exist.yaml")


def test_load_task_rejects_extra_fields(tmp_path: Path):
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "id: bad\n"
        "category: TOOL_SELECTION\n"
        "environment: weather\n"
        "language_variant: EN_EN\n"
        "prompt: hello\n"
        "available_tools: []\n"
        "initial_state_path: states/empty.json\n"
        "expected_final_state: {}\n"
        "rogue_field: 1\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        load_task(bad)


def test_load_task_rejects_invalid_yaml(tmp_path: Path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("id: : :\n  - not a mapping\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_task(bad)


def test_task_strict_match_and_hardcoded_state_load(tmp_path: Path):
    f = tmp_path / "ok.yaml"
    f.write_text(
        "id: t1\n"
        "category: TOOL_SELECTION\n"
        "environment: weather\n"
        "language_variant: PL_EN\n"
        "prompt: hello\n"
        "available_tools: []\n"
        "initial_state_path: states/empty.json\n"
        "expected_final_state: {}\n"
        "strict_match: true\n"
        "hardcoded_state:\n"
        "  cities:\n"
        "    Warszawa: {condition: fog}\n",
        encoding="utf-8",
    )
    task = load_task(f)
    assert task.strict_match is True
    assert task.hardcoded_state == {"cities": {"Warszawa": {"condition": "fog"}}}


def test_task_defaults_when_new_fields_absent():
    task = load_task(DUMMY_TASK_PATH)
    assert task.strict_match is False
    assert task.hardcoded_state is None
