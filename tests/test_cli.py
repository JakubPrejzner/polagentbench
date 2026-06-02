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


# ---------------------------------------------------------------------------
# Multi-temperature grid (prompt 03 additions)
# ---------------------------------------------------------------------------


class _TempAwareRunner(_ScriptedRunner):
    """ScriptedRunner that records per-call temperature so we can assert
    the grid path actually mutates the runner between conditions."""

    temperature: float = 0.0

    def __init__(self, scenarios, **kw):
        super().__init__(scenarios, **kw)
        self.temperatures_seen: list[float] = []

    def run_task(self, task, seed):
        self.temperatures_seen.append(float(self.temperature))
        return super().run_task(task, seed)


def test_parse_temperatures_helper():
    import argparse

    assert cli._parse_temperatures("0.0") == [0.0]
    assert cli._parse_temperatures("0.0, 0.3 ,0.7") == [0.0, 0.3, 0.7]
    with pytest.raises(argparse.ArgumentTypeError):
        cli._parse_temperatures("")
    with pytest.raises(argparse.ArgumentTypeError):
        cli._parse_temperatures("hot")


def test_run_suite_grid_executes_full_cartesian_product(tmp_path: Path):
    # 15 task IDs after the prompt 03.5 split (4a/4b/9a/9b + 011/012/013).
    adv_ids = [
        "adv_001", "adv_002", "adv_003", "adv_004a", "adv_004b",
        "adv_005", "adv_006", "adv_007", "adv_008", "adv_009a",
        "adv_009b", "adv_010", "adv_011", "adv_012", "adv_013",
    ]
    runner = _TempAwareRunner({tid: "pass" for tid in adv_ids})
    adv_dir = REPO_ROOT / "tasks" / "adversarial"
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
            str(adv_dir),
            "--seeds",
            "42,43,44",
            "--temperatures",
            "0.0,0.3,0.7",
            "--output",
            str(tmp_path),
        ],
        runner_factory=_factory(runner),
    )
    assert rc == 0
    # 45 tasks (15 adv_* + 30 v3_chain_*) x 3 seeds x 3 temps = 405 trajectories
    assert len(runner.run_log) == 405

    # The runner's temperature was actually mutated between conditions.
    assert sorted(set(runner.temperatures_seen)) == [0.0, 0.3, 0.7]

    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["tasks_total"] == 45
    assert summary["temperatures"] == [0.0, 0.3, 0.7]
    assert summary["seeds"] == [42, 43, 44]
    assert len(summary["conditions"]) == 9  # 3 temps x 3 seeds
    # The canned "pass" trajectory always calls get_weather(Kraków). Only
    # adv_005's oracle (any_tool_called=get_weather + city contains Kraków)
    # is satisfied; the other 44 tasks (incl. all 30 v3_chain_*) fail. So per
    # condition we expect 1/45 passes, and 9 conditions x 1 = 9 total passes.
    for cond in summary["conditions"]:
        assert cond["total"] == 45
        assert cond["passed"] == 1
    assert "by_temperature" in summary["aggregate"]
    assert "overall" in summary["aggregate"]
    assert summary["aggregate"]["overall"]["pass_rate"] == round(9 / 405, 4)


def test_run_suite_grid_persists_temperature_in_trajectory(tmp_path: Path):
    adv_ids = [
        "adv_001", "adv_002", "adv_003", "adv_004a", "adv_004b",
        "adv_005", "adv_006", "adv_007", "adv_008", "adv_009a",
        "adv_009b", "adv_010", "adv_011", "adv_012", "adv_013",
    ]
    runner = _TempAwareRunner({tid: "pass" for tid in adv_ids})
    adv_dir = REPO_ROOT / "tasks" / "adversarial"
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
            str(adv_dir),
            "--seeds",
            "42",
            "--temperatures",
            "0.0,0.3,0.7",
            "--output",
            str(tmp_path),
        ],
        runner_factory=_factory(runner),
    )
    assert rc == 0
    lines = (tmp_path / "trajectories.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 135  # 45 tasks x 1 seed x 3 temps
    # The scripted runner doesn't itself stamp temperature into the
    # Trajectory (that's the LlamaCppRunner's job via agent_loop), so the
    # serialized field is the model default (0.0). We just check the field
    # exists in the schema and round-trips.
    parsed = [json.loads(line) for line in lines]
    assert all("temperature" in p for p in parsed)


def test_temperatures_overrides_singular_temperature(tmp_path: Path):
    """When both --temperature and --temperatures are passed, plural wins."""
    runner = _TempAwareRunner({f"adv_{n:03d}": "pass" for n in range(1, 11)})
    adv_dir = REPO_ROOT / "tasks" / "adversarial"
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
            str(adv_dir),
            "--seeds",
            "42",
            "--temperature",
            "0.5",  # singular — should be ignored
            "--temperatures",
            "0.0,0.7",
            "--output",
            str(tmp_path),
        ],
        runner_factory=_factory(runner),
    )
    assert rc == 0
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["temperatures"] == [0.0, 0.7]
    assert sorted(set(runner.temperatures_seen)) == [0.0, 0.7]


def test_single_temperature_keeps_old_summary_shape(tmp_path: Path):
    """Without --temperatures the summary uses the legacy single-condition shape."""
    runner = _TempAwareRunner({f"weather_smoke_{n:03d}": "pass" for n in range(1, 6)})
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
            "42",
            "--output",
            str(tmp_path),
        ],
        runner_factory=_factory(runner),
    )
    assert rc == 0
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    # Legacy shape: top-level num_passed / num_total / failure_tag_counts
    assert "num_passed" in summary
    assert "conditions" not in summary


def test_format_grid_report_renders_heatmap():
    from polagentbench.eval.smoke import aggregate_grid_summary, format_grid_report

    cells = []
    for temp in [0.0, 0.3]:
        for seed in [42, 43]:
            for tid, passed in [("adv_001", True), ("adv_002", False)]:
                cells.append(
                    {
                        "temperature": temp,
                        "seed": seed,
                        "task_id": tid,
                        "passed": passed,
                        "status": "PASS" if passed else "FAIL",
                        "failure_tags": [] if passed else ["language_leakage"],
                        "trajectory_summary": "x",
                        "latency_ms": 100.0,
                        "repair_applied_steps": 0,
                    }
                )
    summary = aggregate_grid_summary(
        cells,
        model_id="bielik-mini",
        quant_label="Q8_0",
        repair=False,
        temperatures=[0.0, 0.3],
        seeds=[42, 43],
        task_ids=["adv_001", "adv_002"],
    )
    report = format_grid_report(summary)
    assert "Adversarial grid" in report
    assert "adv_001" in report and "adv_002" in report
    assert "T=0.0" in report and "T=0.3" in report
    assert "s42" in report and "s43" in report
    assert "✓" in report and "✗" in report
    assert "language_leakage" in report


# ---------------------------------------------------------------------------
# Git stamping
# ---------------------------------------------------------------------------


def test_git_info_returns_strings_inside_repo():
    info = cli._git_info()
    assert set(info) == {"commit_hash", "git_ref"}
    assert isinstance(info["commit_hash"], str) and info["commit_hash"]
    assert isinstance(info["git_ref"], str) and info["git_ref"]


def test_git_info_falls_back_to_unknown_when_git_missing(
    monkeypatch: pytest.MonkeyPatch,
):
    def _boom(*_a, **_kw):
        raise FileNotFoundError("git not installed")

    monkeypatch.setattr(cli.subprocess, "run", _boom)
    info = cli._git_info()
    assert info == {"commit_hash": "unknown", "git_ref": "unknown"}


def test_run_subcommand_stamps_summary_with_git_info(tmp_path: Path):
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
    assert "commit_hash" in summary and isinstance(summary["commit_hash"], str)
    assert "git_ref" in summary and isinstance(summary["git_ref"], str)
    assert summary["commit_hash"]  # non-empty
    assert summary["git_ref"]


def test_run_suite_grid_stamps_summary_with_git_info(tmp_path: Path):
    runner = _ScriptedRunner({"weather_smoke_001": "pass", "weather_smoke_002": "pass"})
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
            "42",
            "--temperatures",
            "0.0,0.3",
            "--output",
            str(tmp_path),
        ],
        runner_factory=_factory(runner),
    )
    assert rc == 0
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert "commit_hash" in summary and isinstance(summary["commit_hash"], str)
    assert "git_ref" in summary and isinstance(summary["git_ref"], str)
