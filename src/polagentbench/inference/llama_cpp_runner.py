"""Concrete ModelRunner backed by ``llama-cpp-python``.

The actual ``llama_cpp`` import is lazy so the package can be installed and
tested without the optional ``inference`` extra. The interesting *control
flow* — system prompt → completion → parse → tool execution → next message
— lives in :func:`agent_loop`, a module-level function that takes a generic
``complete_chat`` callable. That keeps the core loop unit-testable with
canned responses (see ``tests/test_inference_runner.py``); the
``LlamaCppRunner`` class is a thin shim that supplies the real callable.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from ..environments.base import Environment
from ..protocol import Action, CallTool, FinalAnswer, attempt_repair, parse_action
from ..runner import ModelRunner
from ..types import FailureTag, Task, Trajectory, TrajectoryStep
from .prompts import PromptLanguage, build_system_prompt

__all__ = ["LlamaCppRunner", "agent_loop"]


# ---------------------------------------------------------------------------
# complete_chat callable contract
# ---------------------------------------------------------------------------
#
# A complete_chat takes a list of OpenAI-style chat messages plus a seed and
# returns (text, latency_ms, usage). ``usage`` is optional — pass None when
# the backend doesn't expose token counts.

ChatMessage = dict[str, str]
CompleteChat = Callable[
    [Sequence[ChatMessage], int],
    tuple[str, float, dict[str, int] | None],
]


def _format_tool_result(tool_name: str, observation: dict[str, Any]) -> str:
    return (
        f'<tool_result tool="{tool_name}">\n'
        f"{json.dumps(observation, ensure_ascii=False)}\n"
        f"</tool_result>"
    )


def agent_loop(
    task: Task,
    env: Environment,
    initial_state: dict[str, Any],
    seed: int,
    model_id: str,
    quant_label: str,
    complete_chat: CompleteChat,
    prompt_language: PromptLanguage = "pl",
    repair: bool = False,
) -> Trajectory:
    """Run one task end-to-end and produce a :class:`Trajectory`.

    Pure function over its inputs; never raises on agent misbehaviour.

    When ``repair`` is True, every step's raw output is passed through
    :func:`polagentbench.protocol.attempt_repair` before parsing. If a
    repair fires, ``raw_model_output`` records the *post-repair* text and
    ``raw_model_output_pre_repair`` preserves the original. This lets
    the smoke evaluator distinguish "agent emitted valid JSON" from
    "agent emitted nearly-valid JSON that was patched by the harness".

    ``task.strict_match`` and ``task.hardcoded_state`` are forwarded to
    ``env.reset`` via two reserved keys (``__strict_match`` / ``__overrides``)
    rather than extending the Environment ABC.
    """
    reset_state = dict(initial_state)
    if task.strict_match:
        reset_state["__strict_match"] = True
    if task.hardcoded_state:
        reset_state["__overrides"] = task.hardcoded_state
    env.reset(reset_state)
    system_prompt = build_system_prompt(
        available_tools=task.available_tools,
        language=prompt_language,
        max_steps=task.max_steps,
    )
    messages: list[ChatMessage] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task.prompt},
    ]
    available_tool_names = [t["name"] for t in task.available_tools if "name" in t]

    steps: list[TrajectoryStep] = []
    failure_tags: list[FailureTag] = []
    total_latency_ms = 0.0
    total_tokens = 0
    final_answer_emitted = False

    for step_idx in range(task.max_steps):
        original_text, latency_ms, usage = complete_chat(messages, seed)
        total_latency_ms += latency_ms
        total_tokens += _tokens_used(original_text, usage)

        repaired_text: str | None = None
        if repair:
            repaired_text = attempt_repair(original_text, available_tool_names)
        text_to_parse = repaired_text if repaired_text is not None else original_text
        repair_applied = repaired_text is not None
        pre_repair = original_text if repair_applied else None

        result = parse_action(text_to_parse)
        messages.append({"role": "assistant", "content": original_text})

        if not result.ok:
            steps.append(
                TrajectoryStep(
                    step_idx=step_idx,
                    raw_model_output=text_to_parse,
                    parsed_action=None,
                    parse_error=result.error,
                    tool_result=None,
                    state_after=env.current_state(),
                    latency_ms=latency_ms,
                    repair_applied=repair_applied,
                    raw_model_output_pre_repair=pre_repair,
                )
            )
            continue

        action: Action = result.action  # type: ignore[assignment]

        if isinstance(action, FinalAnswer):
            steps.append(
                TrajectoryStep(
                    step_idx=step_idx,
                    raw_model_output=text_to_parse,
                    parsed_action=action,
                    parse_error=None,
                    tool_result=None,
                    state_after=env.current_state(),
                    latency_ms=latency_ms,
                    repair_applied=repair_applied,
                    raw_model_output_pre_repair=pre_repair,
                )
            )
            final_answer_emitted = True
            break

        # call_tool
        assert isinstance(action, CallTool)
        observation = env.execute_tool(action.tool, action.arguments)
        steps.append(
            TrajectoryStep(
                step_idx=step_idx,
                raw_model_output=text_to_parse,
                parsed_action=action,
                parse_error=None,
                tool_result=observation,
                state_after=env.current_state(),
                latency_ms=latency_ms,
                repair_applied=repair_applied,
                raw_model_output_pre_repair=pre_repair,
            )
        )
        messages.append({"role": "user", "content": _format_tool_result(action.tool, observation)})

    if not final_answer_emitted:
        failure_tags.append(FailureTag.TIMEOUT)

    return Trajectory(
        task_id=task.id,
        model_id=model_id,
        quant=quant_label,
        interface_variant=task.language_variant,
        seed=seed,
        steps=steps,
        final_state=env.current_state(),
        success=final_answer_emitted,
        failure_tags=failure_tags,
        total_latency_ms=total_latency_ms,
        total_tokens=total_tokens,
    )


def _tokens_used(text: str, usage: dict[str, int] | None) -> int:
    if usage is not None:
        prompt = int(usage.get("prompt_tokens", 0) or 0)
        completion = int(usage.get("completion_tokens", 0) or 0)
        if prompt or completion:
            return prompt + completion
    # Rough fallback: ~4 chars per token. Fine for budgeting / logging only.
    return max(1, len(text) // 4)


def _load_initial_state(task: Task) -> dict[str, Any]:
    if task.source_path is None:
        return {}
    path = task.source_path.parent / task.initial_state_path
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


class LlamaCppRunner(ModelRunner):
    """Drives :func:`agent_loop` against a GGUF model loaded via llama.cpp.

    The ``llama_cpp`` dependency is imported lazily so the rest of the
    package — including the test suite — can run without the optional
    ``inference`` extra installed.
    """

    def __init__(
        self,
        model_path: Path | str,
        model_id: str,
        quant_label: str,
        environments: dict[str, Environment],
        n_ctx: int = 8192,
        n_gpu_layers: int = -1,
        verbose: bool = False,
        prompt_language: PromptLanguage = "pl",
        chat_format: str = "chatml",
        max_tokens: int = 512,
        temperature: float = 0.0,
        top_p: float = 1.0,
        repair: bool = False,
    ) -> None:
        self.model_path = Path(model_path)
        self._model_id = model_id
        self._quant_label = quant_label
        self.environments = environments
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self.verbose = verbose
        self.prompt_language: PromptLanguage = prompt_language
        self.chat_format = chat_format
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.repair = repair
        self._llm: Any | None = None  # llama_cpp.Llama, lazily constructed

    # ------------------------------------------------------------------
    # ModelRunner ABC
    # ------------------------------------------------------------------

    def model_id(self) -> str:
        return self._model_id

    def quant_label(self) -> str:
        return self._quant_label

    def run_task(self, task: Task, seed: int) -> Trajectory:
        env = self.environments.get(task.environment)
        if env is None:
            raise ValueError(
                f"task {task.id!r} requires environment {task.environment!r}, "
                f"which is not registered. Available: {sorted(self.environments)}."
            )
        initial_state = _load_initial_state(task)
        return agent_loop(
            task=task,
            env=env,
            initial_state=initial_state,
            seed=seed,
            model_id=self._model_id,
            quant_label=self._quant_label,
            complete_chat=self._complete_chat,
            prompt_language=self.prompt_language,
            repair=self.repair,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _ensure_llm(self) -> Any:
        if self._llm is None:
            try:
                from llama_cpp import Llama  # type: ignore[import-not-found]
            except ImportError as exc:
                raise RuntimeError(
                    "llama-cpp-python is not installed. Reinstall with "
                    "`uv sync --extra inference` to use LlamaCppRunner."
                ) from exc
            self._llm = Llama(
                model_path=str(self.model_path),
                n_ctx=self.n_ctx,
                n_gpu_layers=self.n_gpu_layers,
                chat_format=self.chat_format,
                verbose=self.verbose,
            )
        return self._llm

    def _complete_chat(
        self, messages: Sequence[ChatMessage], seed: int
    ) -> tuple[str, float, dict[str, int] | None]:
        llm = self._ensure_llm()
        t0 = time.perf_counter()
        response = llm.create_chat_completion(
            messages=list(messages),
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
            seed=seed,
        )
        latency_ms = (time.perf_counter() - t0) * 1000.0
        try:
            text = response["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError):
            text = ""
        usage = response.get("usage") if isinstance(response, dict) else None
        return text, latency_ms, usage
