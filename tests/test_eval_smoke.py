"""Tests for the smoke evaluator.

Builds Trajectory objects directly (skipping the runner) so the evaluator's
behaviour can be tested in isolation against canned step sequences.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from polagentbench.eval.smoke import (
    SmokeStatus,
    aggregate_summary,
    evaluate,
    format_console_report,
)
from polagentbench.protocol import CallTool, FinalAnswer
from polagentbench.types import (
    FailureTag,
    InterfaceVariant,
    Task,
    TaskCategory,
    Trajectory,
    TrajectoryStep,
)


def _task(expected_final_state: dict, tid: str = "t") -> Task:
    return Task(
        id=tid,
        category=TaskCategory.TOOL_SELECTION,
        environment="weather",
        language_variant=InterfaceVariant.PL_EN,
        prompt="x",
        available_tools=[],
        initial_state_path=Path("states/empty.json"),
        expected_final_state=expected_final_state,
        max_steps=4,
    )


def _step_call(idx: int, tool: str, **args) -> TrajectoryStep:
    return TrajectoryStep(
        step_idx=idx,
        raw_model_output="<canned>",
        parsed_action=CallTool(action="call_tool", tool=tool, arguments=args),
        parse_error=None,
        tool_result={"ok": True, "result": {}},
        state_after={},
        latency_ms=1.0,
    )


def _step_final(idx: int, answer: str = "ok") -> TrajectoryStep:
    return TrajectoryStep(
        step_idx=idx,
        raw_model_output="<canned>",
        parsed_action=FinalAnswer(action="final_answer", answer=answer),
        parse_error=None,
        tool_result=None,
        state_after={},
        latency_ms=1.0,
    )


def _trajectory(
    steps: list[TrajectoryStep], failure_tags: list[FailureTag] | None = None
) -> Trajectory:
    return Trajectory(
        task_id="t",
        model_id="m",
        quant="Q8_0",
        interface_variant=InterfaceVariant.PL_EN,
        seed=0,
        steps=steps,
        final_state={},
        success=any(isinstance(s.parsed_action, FinalAnswer) for s in steps),
        failure_tags=failure_tags or [],
        total_latency_ms=sum(s.latency_ms for s in steps),
        total_tokens=0,
    )


def test_pass_when_all_checks_match():
    task = _task(
        {
            "any_tool_called": "get_weather",
            "tool_args_contains": {"city": "Kraków"},
            "final_answer_used": True,
        }
    )
    traj = _trajectory(
        [
            _step_call(0, "get_weather", city="Kraków"),
            _step_final(1, "Pogoda wynosi 7 stopni."),
        ]
    )
    res = evaluate(task, traj)
    assert res.status is SmokeStatus.PASS
    assert res.success is True


def test_fail_when_expected_tool_not_called():
    task = _task({"any_tool_called": "get_weather"})
    traj = _trajectory([_step_call(0, "send_weather_alert", city="x", severity="low", message="m")])
    res = evaluate(task, traj)
    assert res.status is SmokeStatus.FAIL
    assert "expected_tool_not_called" in res.failure_tags


def test_diacritic_insensitive_arg_match():
    task = _task({"tool_args_contains": {"city": "Kraków"}})
    traj = _trajectory([_step_call(0, "get_weather", city="Krakow")])
    res = evaluate(task, traj)
    assert res.status is SmokeStatus.PASS


def test_language_leakage_detected_on_polish_enum_value():
    task = _task(
        {
            "any_tool_called": "send_weather_alert",
            "tool_args_contains": {"severity": "high"},
        }
    )
    traj = _trajectory(
        [_step_call(0, "send_weather_alert", city="Warszawa", severity="wysoka", message="Burza.")]
    )
    res = evaluate(task, traj)
    assert res.status is SmokeStatus.FAIL
    assert "language_leakage" in res.failure_tags


def test_ordered_tools_correct_order_passes():
    task = _task({"ordered_tools": ["get_weather", "convert_temperature"]})
    traj = _trajectory(
        [
            _step_call(0, "get_weather", city="Zakopane"),
            _step_call(
                1, "convert_temperature", value=2.0, from_unit="celsius", to_unit="fahrenheit"
            ),
            _step_final(2),
        ]
    )
    res = evaluate(task, traj)
    assert res.status is SmokeStatus.PASS


def test_ordered_tools_wrong_order_fails():
    task = _task({"ordered_tools": ["get_weather", "convert_temperature"]})
    traj = _trajectory(
        [
            _step_call(
                0, "convert_temperature", value=2.0, from_unit="celsius", to_unit="fahrenheit"
            ),
            _step_call(1, "get_weather", city="Zakopane"),
        ]
    )
    res = evaluate(task, traj)
    assert res.status is SmokeStatus.FAIL
    assert "wrong_tool_order" in res.failure_tags


def test_min_tool_calls_threshold():
    task = _task({"min_tool_calls": {"get_weather": 2}})
    traj_one = _trajectory([_step_call(0, "get_weather", city="Łódź")])
    res_one = evaluate(task, traj_one)
    assert res_one.status is SmokeStatus.FAIL
    assert "insufficient_tool_calls" in res_one.failure_tags

    traj_two = _trajectory(
        [
            _step_call(0, "get_weather", city="Łódź"),
            _step_call(1, "get_weather", city="Świnoujście"),
        ]
    )
    res_two = evaluate(task, traj_two)
    assert res_two.status is SmokeStatus.PASS


def test_final_answer_no_temperature_flags_hallucination():
    task = _task(
        {
            "any_tool_called": "get_weather",
            "final_answer_used": True,
            "final_answer_no_temperature": True,
        }
    )
    traj = _trajectory(
        [
            _step_call(0, "get_weather", city="Atlantis"),
            _step_final(1, "W Atlantis jest 22°C i słonecznie."),
        ]
    )
    res = evaluate(task, traj)
    assert res.status is SmokeStatus.FAIL
    assert "hallucinated_temperature" in res.failure_tags


def test_final_answer_no_temperature_passes_when_clean():
    task = _task(
        {
            "any_tool_called": "get_weather",
            "final_answer_used": True,
            "final_answer_no_temperature": True,
        }
    )
    traj = _trajectory(
        [
            _step_call(0, "get_weather", city="Atlantis"),
            _step_final(1, "Nie znaleziono miasta Atlantis."),
        ]
    )
    res = evaluate(task, traj)
    assert res.status is SmokeStatus.PASS


def test_inconclusive_when_no_recognised_checks():
    task = _task({"some_unknown_check": 1})
    traj = _trajectory([_step_final(0)])
    res = evaluate(task, traj)
    assert res.status is SmokeStatus.INCONCLUSIVE
    assert "inconclusive" in res.failure_tags


def test_parse_errors_surface_in_tags():
    task = _task({"final_answer_used": True})
    bad_step = TrajectoryStep(
        step_idx=0,
        raw_model_output="not json",
        parsed_action=None,
        parse_error={"category": "no_json_found", "message": "x"},  # type: ignore[arg-type]
        tool_result=None,
        state_after={},
        latency_ms=1.0,
    )
    final = _step_final(1)
    traj = _trajectory([bad_step, final])
    res = evaluate(task, traj)
    # Final answer was emitted, so the only failure is the recorded parse error
    assert res.status is SmokeStatus.FAIL
    assert "no_json_found" in res.failure_tags


def test_summary_reports_one_line_per_step():
    task = _task({"any_tool_called": "get_weather"})
    traj = _trajectory(
        [
            _step_call(0, "get_weather", city="Kraków"),
            _step_final(1, "ok"),
        ]
    )
    res = evaluate(task, traj)
    assert "get_weather" in res.trajectory_summary
    assert "final_answer" in res.trajectory_summary


def test_aggregate_summary_counts_failures_across_results():
    task1 = _task({"any_tool_called": "get_weather"})
    task2 = _task(
        {"any_tool_called": "send_weather_alert", "tool_args_contains": {"severity": "high"}},
        tid="t2",
    )
    res1 = evaluate(task1, _trajectory([_step_final(0)]))  # FAIL: tool not called
    res2 = evaluate(
        task2,
        _trajectory(
            [_step_call(0, "send_weather_alert", city="x", severity="wysoka", message="m")]
        ),
    )
    summary = aggregate_summary(
        [res1, res2],
        [_trajectory([], [FailureTag.TIMEOUT])],
        model_id="m",
        quant_label="Q8_0",
    )
    assert summary["num_total"] == 2
    assert summary["num_passed"] == 0
    assert summary["success_rate"] == 0.0
    assert summary["failure_tag_counts"]["expected_tool_not_called"] >= 1
    assert summary["failure_tag_counts"]["language_leakage"] >= 1
    assert summary["failure_tag_counts"]["timeout"] == 1


def test_format_console_report_shape():
    task = _task({"any_tool_called": "get_weather"})
    res = evaluate(task, _trajectory([_step_call(0, "get_weather", city="Kraków"), _step_final(1)]))
    report = format_console_report([res], model_id="m", quant_label="Q", seed=42)
    assert "Smoke test results" in report
    assert "Success: 1/1" in report
    assert res.task_id in report


def test_loose_match_handles_non_string_args():
    task = _task({"tool_args_contains": {"days": 3}})
    traj_match = _trajectory([_step_call(0, "get_forecast", city="x", days=3)])
    traj_miss = _trajectory([_step_call(0, "get_forecast", city="x", days=5)])
    assert evaluate(task, traj_match).status is SmokeStatus.PASS
    assert evaluate(task, traj_miss).status is SmokeStatus.FAIL


@pytest.mark.parametrize(
    "answer,should_flag",
    [
        ("It's 22°C outside.", True),
        ("Aktualna temperatura: 14,5 °C.", True),
        ("Temperature reads 70°F.", True),
        ("It is twenty-two degrees outside.", False),
        ("Nie znaleziono miasta.", False),
    ],
)
def test_temperature_regex(answer: str, should_flag: bool):
    task = _task({"final_answer_used": True, "final_answer_no_temperature": True})
    traj = _trajectory([_step_final(0, answer)])
    res = evaluate(task, traj)
    flagged = "hallucinated_temperature" in res.failure_tags
    assert flagged == should_flag


# ---------------------------------------------------------------------------
# unauthorized_side_effect_for
# ---------------------------------------------------------------------------


def _failed_call_step(idx: int, tool: str) -> TrajectoryStep:
    """Tool was *attempted* (parsed_action set) but the env rejected it."""
    return TrajectoryStep(
        step_idx=idx,
        raw_model_output="<canned>",
        parsed_action=CallTool(action="call_tool", tool=tool, arguments={}),
        parse_error=None,
        tool_result={"ok": False, "error": "x", "error_code": "INVALID_ARGUMENT"},
        state_after={},
        latency_ms=1.0,
    )


def test_unauthorized_side_effect_flags_smoke_003_pattern():
    """Final answer claims alert sent; trajectory has no successful call."""
    task = _task(
        {
            "any_tool_called": "send_weather_alert",
            "unauthorized_side_effect_for": "send_weather_alert",
        }
    )
    # No successful call; the model just hallucinates the side effect in prose.
    traj = _trajectory(
        [
            _step_final(0, "Alarm pogodowy o wysokiej intensywności został wysłany dla Warszawy."),
        ]
    )
    res = evaluate(task, traj)
    assert res.status is SmokeStatus.FAIL
    assert "unauthorized_side_effect" in res.failure_tags


def test_unauthorized_side_effect_passes_when_call_was_successful():
    task = _task(
        {
            "any_tool_called": "send_weather_alert",
            "unauthorized_side_effect_for": "send_weather_alert",
            "final_answer_used": True,
        }
    )
    traj = _trajectory(
        [
            _step_call(0, "send_weather_alert", city="Warszawa", severity="high", message="m"),
            _step_final(1, "Alarm został wysłany."),
        ]
    )
    res = evaluate(task, traj)
    assert res.status is SmokeStatus.PASS


def test_unauthorized_side_effect_skipped_when_no_completion_phrase():
    """If final_answer doesn't actually claim completion, no flag."""
    task = _task(
        {
            "any_tool_called": "send_weather_alert",
            "unauthorized_side_effect_for": "send_weather_alert",
        }
    )
    traj = _trajectory(
        [
            _step_final(0, "Nie udało mi się wysłać alarmu — proszę spróbować ponownie."),
        ]
    )
    res = evaluate(task, traj)
    # any_tool_called still fails — but unauthorized_side_effect should NOT.
    assert "unauthorized_side_effect" not in res.failure_tags


def test_unauthorized_side_effect_failed_call_doesnt_count_as_successful():
    """A call_tool that the env rejected does not count as successful."""
    task = _task({"unauthorized_side_effect_for": "send_weather_alert"})
    traj = _trajectory(
        [
            _failed_call_step(0, "send_weather_alert"),
            _step_final(1, "Alarm został wysłany."),
        ]
    )
    res = evaluate(task, traj)
    assert "unauthorized_side_effect" in res.failure_tags


@pytest.mark.parametrize(
    "answer,should_flag",
    [
        ("Alarm został wysłany.", True),
        ("Wysłałem alert dla Warszawy.", True),
        ("Wysłano alarm pogodowy.", True),
        ("Udało się zrealizować zadanie.", True),
        ("Nie wysłano żadnego alertu.", False),
        ("Brak danych dla tego miasta.", False),
    ],
)
def test_unauthorized_side_effect_phrase_detection(answer: str, should_flag: bool):
    task = _task({"unauthorized_side_effect_for": "send_weather_alert"})
    traj = _trajectory([_step_final(0, answer)])
    res = evaluate(task, traj)
    flagged = "unauthorized_side_effect" in res.failure_tags
    assert flagged == should_flag
