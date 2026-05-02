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


def test_pl_prompt_contains_polish_text():
    prompt = build_system_prompt(WEATHER_TOOLS, language="pl")
    # Spot-check for the rule about emitting JSON only in Polish.
    assert "Wypisz" in prompt or "wypisz" in prompt
    assert "JSON" in prompt


def test_en_prompt_contains_english_text():
    prompt = build_system_prompt(WEATHER_TOOLS, language="en")
    assert "tool-using agent" in prompt
    assert "JSON" in prompt
    assert "get_weather" in prompt


def test_prompt_mentions_max_steps():
    prompt = build_system_prompt(WEATHER_TOOLS, language="pl", max_steps=11)
    assert "11" in prompt


def test_prompt_under_token_budget():
    prompt = build_system_prompt(WEATHER_TOOLS, language="pl")
    # Loose 4-chars-per-token estimate; 800 tokens -> ~3200 chars.
    assert len(prompt) < 3200


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
