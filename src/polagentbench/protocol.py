"""Universal action protocol for PolAgentBench.

Every model under evaluation — regardless of whether it natively supports tool
calling — emits text that the harness parses into one of two action types:

* ``call_tool``: the model wants the harness to execute a tool with given
  arguments.
* ``final_answer``: the model is done and is returning a natural-language reply
  to the user.

Using a *universal* protocol (rather than each vendor's native tool-calling
format) keeps comparisons across model families apples-to-apples and isolates
the variable we actually care about (quantization x language interface)
from differences in tool-call grammars.

The parser in :func:`parse_action` is intentionally tolerant of common
formatting noise produced by instruction-tuned LLMs (markdown code fences,
prose surrounding the JSON object) but strict about the schema itself: any
unexpected field is rejected.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

__all__ = [
    "Action",
    "ActionResult",
    "CallTool",
    "FinalAnswer",
    "ParseError",
    "ParseErrorCategory",
    "attempt_repair",
    "parse_action",
]


class CallTool(BaseModel):
    """Model action: invoke a named tool with structured arguments.

    Attributes:
        action: Discriminator literal, always ``"call_tool"``.
        tool: Name of the tool to invoke. Must be a non-empty string.
        arguments: JSON-serializable keyword arguments to pass to the tool.
            May be an empty dict but must always be a mapping.
    """

    model_config = ConfigDict(extra="forbid")

    action: Literal["call_tool"]
    tool: str = Field(min_length=1, description="Name of the tool to invoke.")
    arguments: dict[str, Any] = Field(
        default_factory=dict,
        description="Keyword arguments for the tool. May be empty but must be a dict.",
    )


class FinalAnswer(BaseModel):
    """Model action: terminate the trajectory with a natural-language reply.

    Attributes:
        action: Discriminator literal, always ``"final_answer"``.
        answer: Natural-language response shown to the user. Non-empty.
    """

    model_config = ConfigDict(extra="forbid")

    action: Literal["final_answer"]
    answer: str = Field(min_length=1, description="Final natural-language reply.")


Action = Annotated[CallTool | FinalAnswer, Field(discriminator="action")]
"""Discriminated union of all valid model actions."""

_ACTION_ADAPTER: TypeAdapter[Action] = TypeAdapter(Action)


ParseErrorCategory = Literal[
    "no_json_found",
    "invalid_json",
    "schema_violation",
    "unknown_action",
]
"""Categories of failure returned by :func:`parse_action`.

* ``no_json_found``: no JSON object could be located in the model output.
* ``invalid_json``: a candidate substring was located but is not valid JSON.
* ``unknown_action``: JSON parsed but ``action`` is not one of the known types.
* ``schema_violation``: ``action`` is recognised but a required field is
  missing, malformed, or an unexpected field is present.
"""


@dataclass(frozen=True)
class ParseError:
    """Structured error returned when an action could not be parsed.

    Attributes:
        category: One of :data:`ParseErrorCategory`.
        message: Human-readable description for logs / debugging.
    """

    category: ParseErrorCategory
    message: str


@dataclass(frozen=True)
class ActionResult:
    """Result of :func:`parse_action`.

    Exactly one of ``action`` or ``error`` is set. Use :attr:`ok` to branch.
    """

    action: Action | None = None
    error: ParseError | None = None

    @property
    def ok(self) -> bool:
        """True if parsing succeeded and ``action`` is populated."""
        return self.action is not None


# Match a fenced code block, optionally tagged ``json``. Captures the body.
_FENCE_RE = re.compile(
    r"```(?:json|JSON)?\s*\n?(.*?)```",
    re.DOTALL,
)


def _extract_json_text(text: str) -> str | None:
    """Locate a JSON object inside arbitrary model output.

    First looks for a fenced code block (```json ... ``` or ``` ... ```).
    Falls back to scanning for the first balanced ``{...}`` substring,
    skipping braces that appear inside JSON strings.

    Returns ``None`` if no candidate substring is found.
    """
    fence = _FENCE_RE.search(text)
    if fence is not None:
        candidate = fence.group(1).strip()
        if candidate:
            return candidate

    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def parse_action(text: str) -> ActionResult:
    """Parse a model's raw output into an :class:`Action` or a :class:`ParseError`.

    This function never raises. On failure it returns an :class:`ActionResult`
    whose ``error`` field carries a :class:`ParseError` with one of the
    categories listed in :data:`ParseErrorCategory`.

    The parser is tolerant of:

    * Surrounding prose ("Here is the action: { ... }").
    * Markdown code fences with or without a ``json`` language tag.

    It is strict about the schema: extra fields cause ``schema_violation``.
    """
    json_text = _extract_json_text(text)
    if json_text is None:
        return ActionResult(
            error=ParseError(
                category="no_json_found",
                message="No JSON object found in model output.",
            )
        )

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as exc:
        return ActionResult(
            error=ParseError(
                category="invalid_json",
                message=f"JSON decode error: {exc.msg} (line {exc.lineno}, col {exc.colno})",
            )
        )

    if not isinstance(data, dict):
        return ActionResult(
            error=ParseError(
                category="invalid_json",
                message="Top-level JSON value must be an object.",
            )
        )

    action_name = data.get("action")
    if action_name not in ("call_tool", "final_answer"):
        return ActionResult(
            error=ParseError(
                category="unknown_action",
                message=f"Unknown or missing action type: {action_name!r}.",
            )
        )

    try:
        action: Action = _ACTION_ADAPTER.validate_python(data)
    except ValidationError as exc:
        return ActionResult(
            error=ParseError(
                category="schema_violation",
                message=str(exc),
            )
        )

    return ActionResult(action=action)


# ---------------------------------------------------------------------------
# Opt-in repair pass
# ---------------------------------------------------------------------------


def attempt_repair(text: str, available_tools: list[str]) -> str | None:
    """Best-effort repair of a single, narrow protocol-violation pattern.

    Currently fixes exactly one shape::

        {"action": "<tool_name>", "arguments": {...}}

    by rewriting it to::

        {"action": "call_tool", "tool": "<tool_name>", "arguments": {...}}

    when ``<tool_name>`` is in ``available_tools``. This is the failure
    mode observed in the prompt 02.5 smoke run, where the model used the
    tool name as the discriminator value instead of as the ``tool`` field.
    The model often hallucinated a side effect immediately after, so left
    unrepaired it bleeds into ``UNAUTHORIZED_SIDE_EFFECT`` territory.

    Repair semantics:

    * Returns the rewritten *full* text on success — not just the JSON
      substring — so downstream parsing keeps the original surrounding
      prose discarded by ``parse_action``'s extraction step regardless.
      In practice the parser ignores everything outside the JSON object,
      so we just emit the canonical JSON.
    * Returns ``None`` whenever the repair can't be applied unambiguously:
      no JSON found, invalid JSON, action already valid, action not in
      ``available_tools``, or a conflicting ``tool`` field disagrees with
      the discriminator.
    * Pure function: no I/O, no global state.
    * Idempotent: applying ``attempt_repair`` to its own output returns
      ``None`` (the result is already valid), so ``repair(repair(x) or x)``
      is stable.

    Out of scope for this pass: missing JSON, markdown fences, missing
    fields beyond the discriminator, schema-shape mismatches. Those would
    each be separate, separately-flagged repairs.
    """
    json_text = _extract_json_text(text)
    if json_text is None:
        return None
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None

    action_name = data.get("action")
    if action_name in ("call_tool", "final_answer"):
        return None  # already valid; no repair needed
    if not isinstance(action_name, str) or action_name not in available_tools:
        return None

    # If the model also wrote a tool field that disagrees with the
    # discriminator we don't know which one it really meant — bail out
    # rather than silently picking one.
    explicit_tool = data.get("tool")
    if explicit_tool is not None and explicit_tool != action_name:
        return None

    arguments = data.get("arguments", {})
    if not isinstance(arguments, dict):
        return None

    repaired = {
        "action": "call_tool",
        "tool": action_name,
        "arguments": arguments,
    }
    return json.dumps(repaired, ensure_ascii=False)
