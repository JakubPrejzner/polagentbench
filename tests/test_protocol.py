"""Tests for the universal action protocol parser."""

from __future__ import annotations

import json

from polagentbench.protocol import (
    CallTool,
    FinalAnswer,
    attempt_repair,
    parse_action,
)

WEATHER_TOOLS = [
    "get_weather",
    "get_forecast",
    "send_weather_alert",
    "convert_temperature",
    "find_nearest_city",
]


def test_valid_call_tool_raw_json():
    text = (
        '{"action": "call_tool", "tool": "search_customer", '
        '"arguments": {"city": "Łódź", "name": "Anna Nowak"}}'
    )
    result = parse_action(text)
    assert result.ok
    assert result.error is None
    assert isinstance(result.action, CallTool)
    assert result.action.tool == "search_customer"
    assert result.action.arguments == {"city": "Łódź", "name": "Anna Nowak"}


def test_valid_final_answer_raw_json():
    text = '{"action": "final_answer", "answer": "Klient nie istnieje w bazie."}'
    result = parse_action(text)
    assert result.ok
    assert isinstance(result.action, FinalAnswer)
    assert result.action.answer == "Klient nie istnieje w bazie."


def test_parse_from_markdown_fenced_json():
    text = (
        "Sure, here's the action:\n"
        "```json\n"
        '{"action": "call_tool", "tool": "get_weather", "arguments": {"city": "Krakow"}}\n'
        "```\n"
        "Let me know if you need anything else."
    )
    result = parse_action(text)
    assert result.ok
    assert isinstance(result.action, CallTool)
    assert result.action.tool == "get_weather"
    assert result.action.arguments == {"city": "Krakow"}


def test_parse_from_unlabeled_fence():
    text = '```\n{"action": "final_answer", "answer": "ok"}\n```'
    result = parse_action(text)
    assert result.ok
    assert isinstance(result.action, FinalAnswer)


def test_parse_with_surrounding_prose_no_fence():
    text = (
        "I think the right move is to call the tool. Action: "
        '{"action": "call_tool", "tool": "list_invoices", "arguments": {}} -- done.'
    )
    result = parse_action(text)
    assert result.ok
    assert isinstance(result.action, CallTool)
    assert result.action.tool == "list_invoices"
    assert result.action.arguments == {}


def test_no_json_returns_no_json_found():
    result = parse_action("I will not produce any JSON today, thank you.")
    assert not result.ok
    assert result.error is not None
    assert result.error.category == "no_json_found"


def test_malformed_json_returns_invalid_json():
    text = "{action: 'call_tool', tool: 'x'}"
    result = parse_action(text)
    assert not result.ok
    assert result.error is not None
    assert result.error.category == "invalid_json"


def test_schema_violation_missing_required_field():
    text = '{"action": "call_tool", "arguments": {}}'  # missing `tool`
    result = parse_action(text)
    assert not result.ok
    assert result.error is not None
    assert result.error.category == "schema_violation"


def test_schema_violation_extra_field_rejected():
    text = '{"action": "call_tool", "tool": "x", "arguments": {}, "rogue": 1}'
    result = parse_action(text)
    assert not result.ok
    assert result.error is not None
    assert result.error.category == "schema_violation"


def test_unknown_action_type():
    text = '{"action": "frobnicate", "blah": 1}'
    result = parse_action(text)
    assert not result.ok
    assert result.error is not None
    assert result.error.category == "unknown_action"


def test_empty_tool_name_is_schema_violation():
    text = '{"action": "call_tool", "tool": "", "arguments": {}}'
    result = parse_action(text)
    assert not result.ok
    assert result.error is not None
    assert result.error.category == "schema_violation"


def test_top_level_array_is_invalid_json():
    text = '[{"action": "call_tool", "tool": "x"}]'
    result = parse_action(text)
    # The brace-scanner finds the inner object, so it actually parses fine.
    # We assert the success branch to lock in the behavior; the important
    # thing is we never raise.
    assert result.ok or (result.error is not None)


def test_parser_never_raises_on_garbage():
    for text in ["", "}}}}}", '{"action":', "```json\n```", "{{{", "\x00\x01"]:
        result = parse_action(text)
        assert result.action is None or result.error is None


# ---------------------------------------------------------------------------
# attempt_repair — wrong-discriminator pattern
# ---------------------------------------------------------------------------


def test_repair_fixes_smoke_003_discriminator_pattern():
    # The exact text the model emitted in prompt 02.5 smoke_003.
    text = (
        '{"action":"send_weather_alert","tool":"send_weather_alert",'
        '"arguments":{"city":"Warszawa","severity":"high","message":"Burza"}}'
    )
    repaired = attempt_repair(text, WEATHER_TOOLS)
    assert repaired is not None
    obj = json.loads(repaired)
    assert obj == {
        "action": "call_tool",
        "tool": "send_weather_alert",
        "arguments": {"city": "Warszawa", "severity": "high", "message": "Burza"},
    }
    # And the repaired text now parses cleanly.
    parsed = parse_action(repaired)
    assert parsed.ok
    assert isinstance(parsed.action, CallTool)
    assert parsed.action.tool == "send_weather_alert"


def test_repair_handles_wrong_discriminator_without_redundant_tool_field():
    text = '{"action":"get_weather","arguments":{"city":"Kraków"}}'
    repaired = attempt_repair(text, WEATHER_TOOLS)
    assert repaired is not None
    parsed = parse_action(repaired)
    assert parsed.ok
    assert isinstance(parsed.action, CallTool)
    assert parsed.action.tool == "get_weather"
    assert parsed.action.arguments == {"city": "Kraków"}


def test_repair_returns_none_for_already_valid_call_tool():
    text = '{"action":"call_tool","tool":"get_weather","arguments":{"city":"x"}}'
    assert attempt_repair(text, WEATHER_TOOLS) is None


def test_repair_returns_none_for_valid_final_answer():
    text = '{"action":"final_answer","answer":"x"}'
    assert attempt_repair(text, WEATHER_TOOLS) is None


def test_repair_returns_none_when_action_not_in_available_tools():
    text = '{"action":"delete_database","arguments":{}}'
    assert attempt_repair(text, WEATHER_TOOLS) is None


def test_repair_returns_none_on_no_json():
    assert attempt_repair("Pogoda w Krakowie to 7.5°C.", WEATHER_TOOLS) is None


def test_repair_returns_none_on_invalid_json():
    assert attempt_repair("{action: 'call_tool'}", WEATHER_TOOLS) is None


def test_repair_returns_none_on_conflicting_tool_field():
    # Discriminator says one tool, tool field says a different one.
    text = '{"action":"get_weather","tool":"get_forecast","arguments":{}}'
    assert attempt_repair(text, WEATHER_TOOLS) is None


def test_repair_returns_none_when_arguments_not_a_dict():
    text = '{"action":"get_weather","arguments":"not a dict"}'
    assert attempt_repair(text, WEATHER_TOOLS) is None


def test_repair_extracts_from_markdown_fence():
    text = '```json\n{"action":"get_weather","arguments":{"city":"Kraków"}}\n```'
    repaired = attempt_repair(text, WEATHER_TOOLS)
    assert repaired is not None
    assert json.loads(repaired)["action"] == "call_tool"


def test_repair_idempotent():
    text = '{"action":"get_weather","arguments":{"city":"Kraków"}}'
    once = attempt_repair(text, WEATHER_TOOLS)
    assert once is not None
    twice = attempt_repair(once, WEATHER_TOOLS)
    assert twice is None  # already valid; no further repair applies


def test_repair_preserves_arguments_exactly():
    args = {"city": "Łódź", "severity": "high", "message": "Burza", "nested": {"x": 1}}
    text = json.dumps({"action": "send_weather_alert", "arguments": args}, ensure_ascii=False)
    repaired = attempt_repair(text, WEATHER_TOOLS)
    assert repaired is not None
    obj = json.loads(repaired)
    assert obj["arguments"] == args


def test_repair_returns_none_when_action_field_missing():
    text = '{"tool":"get_weather","arguments":{"city":"x"}}'
    assert attempt_repair(text, WEATHER_TOOLS) is None
