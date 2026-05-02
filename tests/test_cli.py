"""CLI tests.

Cover argparse plumbing and the suite-runner glue with a mock ModelRunner —
no llama.cpp, no real model.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from polagentbench import cli
from polagentbench.environments.base import Environment
from polagentbench.runner import ModelRunner
from polagentbench.types import (
    FailureTag,
    InterfaceVariant,
    Task,
    Trajectory,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
SMOKE_DIR = REPO_ROOT / "tasks" / "smoke"


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class _ScriptedRunner(ModelRunner):
    """Returns a different canned trajectory per task id."""

    def __init__(self, scenarios: dict[str, str], model_id: str = "fake", quant: str = "Q") -> None:
        self._scenarios = scenarios
        self._model_id = model_id
        self._quant = quant
        self.run_log: list[tuple[str, int]] = []

    def model_id(self) -> str:
        return self._model_id

    def quant_label(self) -> str:
        return self._quant

    def run_task(self, task: Task, seed: int) -> Trajectory:
        self.run_log.append((task.id, seed))
        scenario = self._scenarios.get(task.id, "pass")
        if scenario == "pass":
            from polagentbench.protocol import CallTool, FinalAnswer
            from polagentbench.types import TrajectoryStep

            steps = [
                TrajectoryStep(
                    step_idx=0,
                    raw_model_output="<canned>",
                    parsed_action=CallTool(
                        action="call_tool",
                        tool="get_weather",
                        arguments={"city": "Kraków"},
                    ),
                    parse_error=None,
                    tool_result={"ok": True, "result": {"city": "Kraków", "temperature_c": 7.5}},
                    state_after={},
                    latency_ms=1.0,
                ),
                TrajectoryStep(
                    step_idx=1,
                    raw_model_output="<canned>",
                    parsed_action=FinalAnswer(action="final_answer", answer="ok"),
                    parse_error=None,
                    tool_result=None,
                    state_after={},
                    latency_ms=1.0,
                ),
            ]
            return Trajectory(
                task_id=task.id,
                model_id=self._model_id,
                quant=self._quant,
                interface_variant=InterfaceVariant.PL_EN,
                seed=seed,
                steps=steps,
                final_state={},
                success=True,
                failure_tags=[],
                total_latency_ms=2.0,
                total_tokens=10,
            )
        # scenario == "timeout"
        return Trajectory(
            task_id=task.id,
            model_id=self._model_id,
            quant=self._quant,
            interface_variant=InterfaceVariant.PL_EN,
            seed=seed,
            steps=[],
            final_state={},
            success=False,
            failure_tags=[FailureTag.TIMEOUT],
            total_latency_ms=0.0,
            total_tokens=0,
        )


def _factory(runner: ModelRunner):
    def factory(args, environments: dict[str, Environment]):
        return runner

    return factory


# ---------------------------------------------------------------------------
# Argparse / smoke
# ---------------------------------------------------------------------------


def test_parser_has_run_and_run_suite():
    parser = cli.build_parser()
    args = parser.parse_args(
        [
            "run",
            "--model-path",
            "x.gguf",
            "--model-id",
            "m",
            "--quant",
            "Q8_0",
            "--task",
            str(SMOKE_DIR / "weather_smoke_001.yaml"),
            "--output",
            "out",
        ]
    )
    assert args.command == "run"
    assert args.seed == 42  # default

    args2 = parser.parse_args(
        [
            "run-suite",
            "--model-path",
            "x.gguf",
            "--model-id",
            "m",
            "--quant",
            "Q8_0",
            "--tasks-dir",
            str(SMOKE_DIR),
            "--seeds",
            "42,43",
            "--output",
            "out",
        ]
    )
    assert args2.command == "run-suite"
    assert args2.seeds == "42,43"


def test_main_with_no_args_exits_with_error(capsys: pytest.CaptureFixture[str]):
    with pytest.raises(SystemExit) as excinfo:
        cli.main([])
    assert excinfo.value.code != 0
    err = capsys.readouterr().err
    assert "command" in err.lower() or "required" in err.lower()


def test_run_subcommand_writes_outputs(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    runner = _ScriptedRunner({"weather_smoke_001": "pass"})
    rc = cli.main(
        [
            "run",
            "--model-path",
            "x.gguf",
            "--model-id",
            "fake-m",
            "--quant",
            "Q8_0",
            "--task",
            str(SMOKE_DIR / "weather_smoke_001.yaml"),
            "--output",
            str(tmp_path),
            "--seed",
            "7",
        ],
        runner_factory=_factory(runner),
    )
    assert rc == 0
    assert runner.run_log == [("weather_smoke_001", 7)]

    traj_lines = (tmp_path / "trajectories.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(traj_lines) == 1
    parsed = json.loads(traj_lines[0])
    assert parsed["task_id"] == "weather_smoke_001"
    assert parsed["seed"] == 7

    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["model_id"] == "fake-m"
    assert summary["quant"] == "Q8_0"
    assert summary["num_trajectories"] == 1
    assert summary["num_passed"] == 1

    out = capsys.readouterr().out
    assert "Smoke test results" in out
    assert "weather_smoke_001" in out


def test_run_suite_iterates_tasks_and_seeds(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    scenarios = {
        "weather_smoke_001": "pass",
        "weather_smoke_002": "pass",
        "weather_smoke_003": "timeout",
        "weather_smoke_004": "pass",
        "weather_smoke_005": "pass",
    }
    runner = _ScriptedRunner(scenarios)
    rc = cli.main(
        [
            "run-suite",
            "--model-path",
            "x.gguf",
            "--model-id",
            "fake-m",
            "--quant",
            "Q8_0",
            "--tasks-dir",
            str(SMOKE_DIR),
            "--seeds",
            "11,22",
            "--output",
            str(tmp_path),
        ],
        runner_factory=_factory(runner),
    )
    assert rc == 0
    # 5 tasks x 2 seeds = 10 runs
    assert len(runner.run_log) == 10

    traj_lines = (tmp_path / "trajectories.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(traj_lines) == 10

    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["num_total"] == 10
    assert summary["failure_tag_counts"].get("timeout", 0) == 2


def test_run_suite_errors_on_empty_tasks_dir(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    empty = tmp_path / "empty"
    empty.mkdir()
    rc = cli.main(
        [
            "run-suite",
            "--model-path",
            "x.gguf",
            "--model-id",
            "fake-m",
            "--quant",
            "Q8_0",
            "--tasks-dir",
            str(empty),
            "--seeds",
            "42",
            "--output",
            str(tmp_path / "out"),
        ],
        runner_factory=_factory(_ScriptedRunner({})),
    )
    assert rc == 2


def test_parse_seeds_helper():
    assert cli._parse_seeds("42") == [42]
    assert cli._parse_seeds("1, 2 ,3") == [1, 2, 3]
    import argparse

    with pytest.raises(argparse.ArgumentTypeError):
        cli._parse_seeds("")
    with pytest.raises(argparse.ArgumentTypeError):
        cli._parse_seeds("abc")


def test_environment_registry_includes_weather():
    envs = cli._build_environments()
    assert "weather" in envs
    assert envs["weather"].available_tool_names()


def test_repair_flag_propagates_to_summary(tmp_path: Path):
    runner = _ScriptedRunner({"weather_smoke_001": "pass"})
    rc = cli.main(
        [
            "run",
            "--model-path",
            "x.gguf",
            "--model-id",
            "fake-m",
            "--quant",
            "Q8_0",
            "--task",
            str(SMOKE_DIR / "weather_smoke_001.yaml"),
            "--output",
            str(tmp_path),
            "--seed",
            "7",
            "--repair",
        ],
        runner_factory=_factory(runner),
    )
    assert rc == 0
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["repair"] is True
    assert "repair_applied_steps" in summary


def test_repair_flag_default_off(tmp_path: Path):
    runner = _ScriptedRunner({"weather_smoke_001": "pass"})
    rc = cli.main(
        [
            "run",
            "--model-path",
            "x.gguf",
            "--model-id",
            "fake-m",
            "--quant",
            "Q8_0",
            "--task",
            str(SMOKE_DIR / "weather_smoke_001.yaml"),
            "--output",
            str(tmp_path),
        ],
        runner_factory=_factory(runner),
    )
    assert rc == 0
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["repair"] is False
