"""Tests for the system-prompt builder."""

from __future__ import annotations

import pytest

from polagentbench.inference.prompts import build_system_prompt

WEATHER_TOOLS = [
    {
        "name": "get_weather",
        "description": "Get current weather for a city.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    },
    {
        "name": "send_weather_alert",
        "description": "Send a weather alert.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                "message": {"type": "string"},
            },
            "required": ["city", "severity", "message"],
        },
    },
]


def test_pl_prompt_contains_all_tool_names():
    prompt = build_system_prompt(WEATHER_TOOLS, language="pl", max_steps=8)
    assert "get_weather" in prompt
    assert "send_weather_alert" in prompt


def test_pl_prompt_includes_both_action_examples():
    prompt = build_system_prompt(WEATHER_TOOLS, language="pl")
    assert '"action": "call_tool"' in prompt
    assert '"action": "final_answer"' in prompt


def test_pl_prompt_contains_strict_uppercase_rule():
    prompt = build_system_prompt(WEATHER_TOOLS, language="pl")
    assert "KAŻDA TWOJA ODPOWIEDŹ MUSI BYĆ JEDNYM OBIEKTEM JSON" in prompt
    # The uppercase NIGDY repetitions are part of the strictness signal.
    assert "NIGDY" in prompt


def test_pl_prompt_includes_two_turn_walkthrough():
    prompt = build_system_prompt(WEATHER_TOOLS, language="pl")
    assert "Przykład pełnej trajektorii" in prompt
    assert "Asystent (tura 1)" in prompt
    assert "Asystent (tura 2 - finalna)" in prompt
    # The walkthrough must include a tool_result line so the model sees the
    # exact "JSON-after-tool-result" pattern, not just two unrelated turns.
    assert "<tool_result tool=" in prompt
    assert '"final_answer"' in prompt


def test_pl_prompt_includes_forbidden_patterns_section():
    prompt = build_system_prompt(WEATHER_TOOLS, language="pl")
    assert "ZABRONIONE" in prompt
    assert "DOZWOLONE" in prompt
    assert "proza" in prompt
    assert "markdown" in prompt


def test_en_prompt_contains_english_text():
    prompt = build_system_prompt(WEATHER_TOOLS, language="en")
    assert "tool-using agent" in prompt
    assert "JSON" in prompt
    assert "get_weather" in prompt


def test_en_prompt_mirrors_strict_structure():
    prompt = build_system_prompt(WEATHER_TOOLS, language="en")
    assert "EVERY RESPONSE MUST BE A SINGLE JSON OBJECT" in prompt
    assert "FORBIDDEN" in prompt
    assert "Example trajectory" in prompt


def test_prompt_mentions_max_steps():
    prompt = build_system_prompt(WEATHER_TOOLS, language="pl", max_steps=11)
    assert "11" in prompt


def test_prompt_under_token_budget():
    prompt = build_system_prompt(WEATHER_TOOLS, language="pl")
    # 1500 tokens at the conventional 4-chars-per-token estimate -> 6000 chars.
    estimated_tokens = len(prompt) // 4
    assert estimated_tokens < 1500, f"prompt is {estimated_tokens} tokens (limit 1500)"


def test_unsupported_language_raises():
    with pytest.raises(ValueError):
        build_system_prompt(WEATHER_TOOLS, language="de")  # type: ignore[arg-type]


def test_tool_parameters_rendered():
    prompt = build_system_prompt(WEATHER_TOOLS, language="pl")
    assert '"city"' in prompt
    assert "severity" in prompt


def test_empty_tool_list_does_not_crash():
    prompt = build_system_prompt([], language="pl")
    assert "JSON" in prompt
