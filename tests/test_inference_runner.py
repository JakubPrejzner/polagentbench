"""Tests for the agent loop with a fake ``complete_chat`` callable.

We never load a real model here. The ``complete_chat`` callable is replaced
with a deterministic queue of canned responses, which is enough to exercise
every code path through the loop: parse errors, tool-call → tool-result
threading, final_answer termination, and step-budget exhaustion.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest

from polagentbench.environments.weather import WeatherEnvironment
from polagentbench.inference.llama_cpp_runner import agent_loop
from polagentbench.protocol import CallTool, FinalAnswer
from polagentbench.types import (
    FailureTag,
    InterfaceVariant,
    Task,
    TaskCategory,
)


def _make_task(prompt: str = "Sprawdź pogodę w Krakowie.", max_steps: int = 4) -> Task:
    return Task(
        id="test_task",
        category=TaskCategory.TOOL_SELECTION,
        environment="weather",
        language_variant=InterfaceVariant.PL_EN,
        prompt=prompt,
        available_tools=[
            {
                "name": "get_weather",
                "description": "Get current weather.",
                "parameters": {
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"],
                },
            }
        ],
        initial_state_path=Path("states/empty.json"),
        expected_final_state={},
        max_steps=max_steps,
    )


class CannedChat:
    """A complete_chat that yields a fixed sequence of (text, latency, usage)."""

    def __init__(
        self,
        responses: Sequence[tuple[str, float, dict[str, int] | None]],
    ) -> None:
        self._responses = list(responses)
        self.call_log: list[list[dict[str, str]]] = []

    def __call__(
        self, messages: Sequence[dict[str, str]], seed: int
    ) -> tuple[str, float, dict[str, int] | None]:
        self.call_log.append(list(messages))
        if not self._responses:
            raise AssertionError("CannedChat exhausted")
        return self._responses.pop(0)


def test_happy_path_call_tool_then_final_answer():
    task = _make_task()
    env = WeatherEnvironment()
    chat = CannedChat(
        [
            (
                '{"action":"call_tool","tool":"get_weather","arguments":{"city":"Kraków"}}',
                12.0,
                {"prompt_tokens": 100, "completion_tokens": 20},
            ),
            (
                '{"action":"final_answer","answer":"W Krakowie jest 7.5°C."}',
                8.0,
                {"prompt_tokens": 150, "completion_tokens": 15},
            ),
        ]
    )
    traj = agent_loop(
        task=task,
        env=env,
        initial_state={},
        seed=42,
        model_id="m",
        quant_label="Q8_0",
        complete_chat=chat,
    )
    assert traj.success is True
    assert traj.failure_tags == []
    assert len(traj.steps) == 2
    assert isinstance(traj.steps[0].parsed_action, CallTool)
    assert traj.steps[0].tool_result is not None
    assert traj.steps[0].tool_result["ok"] is True
    assert isinstance(traj.steps[1].parsed_action, FinalAnswer)
    assert traj.total_latency_ms == pytest.approx(20.0)
    assert traj.total_tokens == 100 + 20 + 150 + 15


def test_parse_error_does_not_terminate_loop():
    task = _make_task(max_steps=3)
    env = WeatherEnvironment()
    chat = CannedChat(
        [
            ("I will not produce JSON, sorry.", 5.0, None),
            ('{"action":"final_answer","answer":"ok"}', 5.0, None),
        ]
    )
    traj = agent_loop(
        task=task,
        env=env,
        initial_state={},
        seed=0,
        model_id="m",
        quant_label="q",
        complete_chat=chat,
    )
    assert traj.success is True
    assert traj.steps[0].parse_error is not None
    assert traj.steps[0].parse_error.category == "no_json_found"
    assert traj.steps[0].parsed_action is None
    assert isinstance(traj.steps[1].parsed_action, FinalAnswer)


def test_timeout_when_no_final_answer_within_budget():
    task = _make_task(max_steps=2)
    env = WeatherEnvironment()
    chat = CannedChat(
        [
            (
                '{"action":"call_tool","tool":"get_weather","arguments":{"city":"Kraków"}}',
                1.0,
                None,
            ),
            (
                '{"action":"call_tool","tool":"get_weather","arguments":{"city":"Wrocław"}}',
                1.0,
                None,
            ),
        ]
    )
    traj = agent_loop(
        task=task,
        env=env,
        initial_state={},
        seed=0,
        model_id="m",
        quant_label="q",
        complete_chat=chat,
    )
    assert traj.success is False
    assert FailureTag.TIMEOUT in traj.failure_tags
    assert len(traj.steps) == 2


def test_tool_error_threaded_back_as_user_message():
    task = _make_task()
    env = WeatherEnvironment()
    chat = CannedChat(
        [
            (
                '{"action":"call_tool","tool":"get_weather","arguments":{"city":"Atlantis"}}',
                1.0,
                None,
            ),
            ('{"action":"final_answer","answer":"Nie znaleziono miasta."}', 1.0, None),
        ]
    )
    traj = agent_loop(
        task=task,
        env=env,
        initial_state={},
        seed=0,
        model_id="m",
        quant_label="q",
        complete_chat=chat,
    )
    assert traj.steps[0].tool_result["ok"] is False
    assert traj.steps[0].tool_result["error_code"] == "CITY_NOT_FOUND"
    # The second call's messages should include the tool_result as a user msg
    second_call_messages = chat.call_log[1]
    user_tool_results = [
        m for m in second_call_messages if m["role"] == "user" and "<tool_result" in m["content"]
    ]
    assert len(user_tool_results) == 1
    assert "CITY_NOT_FOUND" in user_tool_results[0]["content"]


def test_token_estimation_when_usage_missing():
    task = _make_task()
    env = WeatherEnvironment()
    chat = CannedChat(
        [
            ('{"action":"final_answer","answer":"' + "x" * 80 + '"}', 1.0, None),
        ]
    )
    traj = agent_loop(
        task=task,
        env=env,
        initial_state={},
        seed=0,
        model_id="m",
        quant_label="q",
        complete_chat=chat,
    )
    # Estimated as len(text) // 4
    assert traj.total_tokens > 20
    assert traj.total_tokens < 200


def test_unknown_environment_in_runner_raises():
    from polagentbench.inference.llama_cpp_runner import LlamaCppRunner

    runner = LlamaCppRunner(
        model_path=Path("/nonexistent/model.gguf"),
        model_id="m",
        quant_label="Q",
        environments={},  # nothing registered
    )
    task = _make_task()
    with pytest.raises(ValueError, match="not registered"):
        runner.run_task(task, seed=0)


def test_runner_errors_on_missing_llama_cpp(monkeypatch: pytest.MonkeyPatch):
    """Without llama-cpp-python installed, _ensure_llm must raise RuntimeError."""
    # Force the lazy import to fail
    import builtins

    from polagentbench.inference import llama_cpp_runner as mod

    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "llama_cpp":
            raise ImportError("simulated missing llama_cpp")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    runner = mod.LlamaCppRunner(
        model_path=Path("x.gguf"),
        model_id="m",
        quant_label="Q",
        environments={"weather": WeatherEnvironment()},
    )
    with pytest.raises(RuntimeError, match="llama-cpp-python"):
        runner._ensure_llm()
