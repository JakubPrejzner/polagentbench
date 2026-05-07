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


# ---------------------------------------------------------------------------
# New oracle keys introduced in prompt 03
# ---------------------------------------------------------------------------


def test_tools_called_in_order_alias_matches_ordered_tools():
    task = _task({"tools_called_in_order": ["get_weather", "convert_temperature"]})
    traj = _trajectory(
        [
            _step_call(0, "get_weather", city="Zakopane"),
            _step_call(1, "convert_temperature", value=2.0, from_unit="celsius", to_unit="fahrenheit"),
            _step_final(2),
        ]
    )
    assert evaluate(task, traj).status is SmokeStatus.PASS


def test_tools_called_in_order_alias_fails_on_wrong_order():
    task = _task({"tools_called_in_order": ["get_weather", "send_weather_alert"]})
    traj = _trajectory(
        [
            _step_call(0, "send_weather_alert", city="x", severity="low", message="m"),
            _step_call(1, "get_weather", city="x"),
        ]
    )
    res = evaluate(task, traj)
    assert res.status is SmokeStatus.FAIL
    assert "wrong_tool_order" in res.failure_tags


def test_max_tool_calls_passes_under_threshold():
    task = _task({"max_tool_calls": {"get_weather": 2}})
    traj = _trajectory(
        [
            _step_call(0, "get_weather", city="Atlantyda"),
            _step_call(1, "get_weather", city="Atlantis"),
            _step_final(2, "Nie znaleziono."),
        ]
    )
    assert evaluate(task, traj).status is SmokeStatus.PASS


def test_max_tool_calls_fails_with_loop_tag_when_over():
    task = _task({"max_tool_calls": {"get_weather": 2}})
    traj = _trajectory(
        [
            _step_call(0, "get_weather", city="x"),
            _step_call(1, "get_weather", city="x"),
            _step_call(2, "get_weather", city="x"),
            _step_final(3),
        ]
    )
    res = evaluate(task, traj)
    assert res.status is SmokeStatus.FAIL
    assert "loop" in res.failure_tags


def test_tool_args_exact_passes_on_strict_match():
    task = _task({"tool_args_exact": {"send_weather_alert": {"severity": "high", "city": "Wrocław"}}})
    traj = _trajectory(
        [_step_call(0, "send_weather_alert", city="Wrocław", severity="high", message="m")]
    )
    assert evaluate(task, traj).status is SmokeStatus.PASS


def test_tool_args_exact_fails_on_diacritic_corruption():
    """Strict equality — folded form does NOT pass (unlike tool_args_contains)."""
    task = _task({"tool_args_exact": {"get_weather": {"city": "Łódź"}}})
    traj = _trajectory([_step_call(0, "get_weather", city="Lodz")])
    res = evaluate(task, traj)
    assert res.status is SmokeStatus.FAIL
    assert "wrong_tool_args" in res.failure_tags


def test_tool_args_exact_flags_language_leakage():
    task = _task({"tool_args_exact": {"send_weather_alert": {"severity": "high"}}})
    traj = _trajectory(
        [_step_call(0, "send_weather_alert", city="Wrocław", severity="wysoka", message="m")]
    )
    res = evaluate(task, traj)
    assert res.status is SmokeStatus.FAIL
    assert "wrong_tool_args" in res.failure_tags
    assert "language_leakage" in res.failure_tags


def test_tool_args_exact_missing_call_tags_expected_tool_not_called():
    task = _task({"tool_args_exact": {"send_weather_alert": {"severity": "high"}}})
    traj = _trajectory([_step_call(0, "get_weather", city="x"), _step_final(1)])
    res = evaluate(task, traj)
    assert res.status is SmokeStatus.FAIL
    assert "expected_tool_not_called" in res.failure_tags


def test_final_answer_contains_any_passes_with_match():
    task = _task({"final_answer_contains_any": ["nie znaleziono", "not found"]})
    traj = _trajectory([_step_final(0, "Niestety, nie znaleziono miasta Atlantyda.")])
    assert evaluate(task, traj).status is SmokeStatus.PASS


def test_final_answer_contains_any_diacritic_insensitive():
    task = _task({"final_answer_contains_any": ["nieznane"]})
    traj = _trajectory([_step_final(0, "Miasto nieznane w bazie.")])
    assert evaluate(task, traj).status is SmokeStatus.PASS


def test_final_answer_contains_any_fails_when_none_present():
    task = _task({"final_answer_contains_any": ["nie znaleziono"]})
    traj = _trajectory([_step_final(0, "Pogoda jest dobra.")])
    res = evaluate(task, traj)
    assert res.status is SmokeStatus.FAIL
    assert "wrong_final_answer" in res.failure_tags


def test_no_tool_calls_passes_when_only_final_answer():
    task = _task({"no_tool_calls": True, "final_answer_used": True})
    traj = _trajectory([_step_final(0, "Krótkie wyjaśnienie.")])
    assert evaluate(task, traj).status is SmokeStatus.PASS


def test_no_tool_calls_fails_when_tool_used():
    task = _task({"no_tool_calls": True})
    traj = _trajectory([_step_call(0, "get_weather", city="x"), _step_final(1)])
    res = evaluate(task, traj)
    assert res.status is SmokeStatus.FAIL
    assert "unexpected_tool_call" in res.failure_tags


def test_hallucinated_tool_result_fires_when_no_call_and_temperature_present():
    task = _task(
        {
            "any_tool_called": "get_weather",
            "hallucinated_tool_result_for": "get_weather",
            "final_answer_used": True,
        }
    )
    traj = _trajectory([_step_final(0, "W Krakowie jest 12°C i słonecznie.")])
    res = evaluate(task, traj)
    assert res.status is SmokeStatus.FAIL
    assert "hallucinated_tool_result" in res.failure_tags


def test_hallucinated_tool_result_silent_when_call_succeeded():
    task = _task(
        {
            "any_tool_called": "get_weather",
            "hallucinated_tool_result_for": "get_weather",
            "final_answer_used": True,
        }
    )
    traj = _trajectory(
        [
            _step_call(0, "get_weather", city="Kraków"),
            _step_final(1, "W Krakowie jest 7.5°C."),
        ]
    )
    res = evaluate(task, traj)
    assert res.status is SmokeStatus.PASS
    assert "hallucinated_tool_result" not in res.failure_tags


def test_hallucinated_tool_result_silent_when_no_temperature_in_answer():
    """Bare 'no, can't help' answer doesn't trip the tag even if call missing."""
    task = _task({"hallucinated_tool_result_for": "get_weather"})
    traj = _trajectory([_step_final(0, "Nie mogę pomóc bez dodatkowych danych.")])
    res = evaluate(task, traj)
    assert "hallucinated_tool_result" not in res.failure_tags


def test_hallucinated_tool_result_dual_tag_with_temperature_check():
    """final_answer_no_temperature now ALSO emits hallucinated_tool_result."""
    task = _task({"final_answer_no_temperature": True})
    traj = _trajectory([_step_final(0, "Aktualnie jest 22°C i słonecznie.")])
    res = evaluate(task, traj)
    assert "hallucinated_temperature" in res.failure_tags
    assert "hallucinated_tool_result" in res.failure_tags


def test_all_tool_calls_succeeded_passes_when_all_ok():
    task = _task({"all_tool_calls_succeeded": True})
    traj = _trajectory(
        [
            _step_call(0, "get_weather", city="Świnoujście"),
            _step_call(1, "get_weather", city="Żory"),
            _step_final(2),
        ]
    )
    assert evaluate(task, traj).status is SmokeStatus.PASS


def test_all_tool_calls_succeeded_fails_on_any_tool_error():
    task = _task({"all_tool_calls_succeeded": True})
    bad = TrajectoryStep(
        step_idx=0,
        raw_model_output="<canned>",
        parsed_action=CallTool(action="call_tool", tool="get_weather", arguments={"city": "Lodz"}),
        parse_error=None,
        tool_result={"ok": False, "error": "x", "error_code": "CITY_NOT_FOUND"},
        state_after={},
        latency_ms=1.0,
    )
    traj = _trajectory([bad, _step_final(1)])
    res = evaluate(task, traj)
    assert res.status is SmokeStatus.FAIL
    assert "tool_call_error" in res.failure_tags


def test_all_tool_calls_succeeded_off_by_default():
    """Spec value False = no-op (does not flag even if calls fail)."""
    task = _task({"all_tool_calls_succeeded": False, "final_answer_used": True})
    bad = TrajectoryStep(
        step_idx=0,
        raw_model_output="<canned>",
        parsed_action=CallTool(action="call_tool", tool="get_weather", arguments={"city": "Lodz"}),
        parse_error=None,
        tool_result={"ok": False, "error": "x", "error_code": "CITY_NOT_FOUND"},
        state_after={},
        latency_ms=1.0,
    )
    traj = _trajectory([bad, _step_final(1)])
    res = evaluate(task, traj)
    assert "tool_call_error" not in res.failure_tags


# ---------------------------------------------------------------------------
# New oracle keys introduced in prompt 03.5
# ---------------------------------------------------------------------------


def test_tools_called_in_order_loose_passes_when_all_items_match_any_order():
    task = _task(
        {
            "tools_called_in_order_loose": [
                {"tool": "get_weather", "args": {"city": "Świnoujście"}},
                {"tool": "get_weather", "args": {"city": "Żory"}},
            ]
        }
    )
    # Reverse order should still pass.
    traj = _trajectory(
        [
            _step_call(0, "get_weather", city="Żory"),
            _step_call(1, "get_weather", city="Świnoujście"),
            _step_final(2),
        ]
    )
    assert evaluate(task, traj).status is SmokeStatus.PASS


def test_tools_called_in_order_loose_fails_when_item_missing():
    task = _task(
        {
            "tools_called_in_order_loose": [
                {"tool": "get_weather", "args": {"city": "Świnoujście"}},
                {"tool": "get_weather", "args": {"city": "Żory"}},
            ]
        }
    )
    traj = _trajectory([_step_call(0, "get_weather", city="Świnoujście"), _step_final(1)])
    res = evaluate(task, traj)
    assert res.status is SmokeStatus.FAIL
    assert "expected_tool_not_called" in res.failure_tags


def test_tools_called_in_order_loose_strict_arg_equality():
    """Diacritic-folded form does NOT match (unlike tool_args_contains)."""
    task = _task(
        {
            "tools_called_in_order_loose": [
                {"tool": "get_weather", "args": {"city": "Łódź"}},
            ]
        }
    )
    traj = _trajectory([_step_call(0, "get_weather", city="Lodz"), _step_final(1)])
    res = evaluate(task, traj)
    assert res.status is SmokeStatus.FAIL
    assert "expected_tool_not_called" in res.failure_tags


def test_tools_called_in_order_loose_extra_args_allowed():
    """Spec only pins ``city``; the call may carry additional arguments."""
    task = _task(
        {
            "tools_called_in_order_loose": [
                {"tool": "send_weather_alert", "args": {"city": "Zakopane", "severity": "low"}},
            ]
        }
    )
    traj = _trajectory(
        [
            _step_call(0, "send_weather_alert", city="Zakopane", severity="low", message="m"),
            _step_final(1),
        ]
    )
    assert evaluate(task, traj).status is SmokeStatus.PASS


def test_tools_called_in_order_strict_passes_in_order():
    task = _task(
        {
            "tools_called_in_order_strict": [
                {"tool": "get_weather", "args": {"city": "Gdańsk"}},
                {"tool": "find_nearest_city", "args": {"reference_city": "Gdańsk", "max_distance_km": 50}},
                {"tool": "get_forecast", "args": {"days": 3}},
            ]
        }
    )
    traj = _trajectory(
        [
            _step_call(0, "get_weather", city="Gdańsk"),
            _step_call(1, "find_nearest_city", reference_city="Gdańsk", max_distance_km=50),
            _step_call(2, "get_forecast", city="Sopot", days=3),
            _step_final(3),
        ]
    )
    assert evaluate(task, traj).status is SmokeStatus.PASS


def test_tools_called_in_order_strict_fails_when_reordered():
    task = _task(
        {
            "tools_called_in_order_strict": [
                {"tool": "get_weather", "args": {"city": "Gdańsk"}},
                {"tool": "find_nearest_city", "args": {"reference_city": "Gdańsk", "max_distance_km": 50}},
            ]
        }
    )
    traj = _trajectory(
        [
            _step_call(0, "find_nearest_city", reference_city="Gdańsk", max_distance_km=50),
            _step_call(1, "get_weather", city="Gdańsk"),
            _step_final(2),
        ]
    )
    res = evaluate(task, traj)
    assert res.status is SmokeStatus.FAIL
    assert "wrong_tool_order" in res.failure_tags


def test_tools_called_in_order_strict_allows_extra_calls_in_between():
    """A 'noise' call between two strict items doesn't break the subsequence match."""
    task = _task(
        {
            "tools_called_in_order_strict": [
                {"tool": "get_weather", "args": {"city": "Gdańsk"}},
                {"tool": "get_forecast", "args": {"days": 3}},
            ]
        }
    )
    traj = _trajectory(
        [
            _step_call(0, "get_weather", city="Gdańsk"),
            _step_call(1, "find_nearest_city", reference_city="Gdańsk", max_distance_km=50),
            _step_call(2, "get_forecast", city="Sopot", days=3),
            _step_final(3),
        ]
    )
    assert evaluate(task, traj).status is SmokeStatus.PASS


def test_tools_called_in_order_strict_fails_with_missing_arg_match():
    task = _task(
        {
            "tools_called_in_order_strict": [
                {"tool": "get_forecast", "args": {"days": 3}},
            ]
        }
    )
    traj = _trajectory([_step_call(0, "get_forecast", city="Kraków", days=5), _step_final(1)])
    res = evaluate(task, traj)
    assert res.status is SmokeStatus.FAIL
    assert "wrong_tool_order" in res.failure_tags


def test_final_answer_is_string_passes_when_answer_is_string():
    task = _task({"final_answer_is_string": True, "final_answer_used": True})
    traj = _trajectory([_step_final(0, "Pogoda jest dobra.")])
    assert evaluate(task, traj).status is SmokeStatus.PASS


def test_final_answer_is_string_flags_dict_answer_via_schema_violation():
    """Pydantic rejects ``answer={...}`` at parse time → schema_violation step.

    The check inspects raw_model_output of schema_violation steps for the
    wrong-shape pattern and emits ``final_answer_shape_violation``.
    """
    task = _task({"final_answer_is_string": True})
    bad_step = TrajectoryStep(
        step_idx=0,
        raw_model_output='{"action": "final_answer", "answer": {"city": "Świnoujście", "temperature_c": 8.0}}',
        parsed_action=None,
        parse_error={"category": "schema_violation", "message": "answer must be string"},  # type: ignore[arg-type]
        tool_result=None,
        state_after={},
        latency_ms=1.0,
    )
    traj = _trajectory([bad_step])
    res = evaluate(task, traj)
    assert res.status is SmokeStatus.FAIL
    assert "final_answer_shape_violation" in res.failure_tags


def test_final_answer_is_string_silent_when_no_attempted_final_answer():
    task = _task({"final_answer_is_string": True, "final_answer_used": True})
    traj = _trajectory([_step_call(0, "get_weather", city="Kraków")])
    res = evaluate(task, traj)
    # final_answer_used should fail (final_answer_missing), but the
    # is_string check should NOT add final_answer_shape_violation since
    # the model never even tried a final_answer.
    assert "final_answer_shape_violation" not in res.failure_tags


def test_final_answer_is_string_off_by_default():
    """spec_value=False is a no-op."""
    task = _task({"final_answer_is_string": False})
    bad_step = TrajectoryStep(
        step_idx=0,
        raw_model_output='{"action": "final_answer", "answer": {"x": 1}}',
        parsed_action=None,
        parse_error={"category": "schema_violation", "message": "x"},  # type: ignore[arg-type]
        tool_result=None,
        state_after={},
        latency_ms=1.0,
    )
    traj = _trajectory([bad_step, _step_final(1)])
    # final_answer_is_string off -> no shape-violation tag from this check.
    # (schema_violation tag from the parse_error step still surfaces, that's
    # a separate behaviour.)
    res = evaluate(task, traj)
    assert "final_answer_shape_violation" not in res.failure_tags


def test_max_tool_calls_zero_blocks_any_call():
    """Acceptance: max_tool_calls={tool: 0} forbids any call to that tool."""
    task = _task(
        {
            "max_tool_calls": {"send_weather_alert": 0},
            "any_tool_called": "get_weather",
        }
    )
    # Calling send_weather_alert at all should fail the 0-threshold.
    traj_fail = _trajectory(
        [
            _step_call(0, "get_weather", city="Wrocław"),
            _step_call(1, "send_weather_alert", city="Wrocław", severity="low", message="m"),
            _step_final(2),
        ]
    )
    res_fail = evaluate(task, traj_fail)
    assert res_fail.status is SmokeStatus.FAIL
    assert "loop" in res_fail.failure_tags

    # Not calling it passes.
    traj_pass = _trajectory(
        [
            _step_call(0, "get_weather", city="Wrocław"),
            _step_final(1, "Słońce — alarm niepotrzebny."),
        ]
    )
    assert evaluate(task, traj_pass).status is SmokeStatus.PASS
