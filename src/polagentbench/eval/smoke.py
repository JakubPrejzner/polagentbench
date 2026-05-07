"""Permissive smoke-test evaluator.

Looks at a trajectory and a task's ``expected_final_state`` block and returns
a :class:`SmokeResult`. The supported expectation keys are deliberately
small and pragmatic — strict oracles come later. Tasks whose expectation
block contains nothing actionable are reported as ``INCONCLUSIVE`` rather
than silently passing.

Recognised expectation keys
---------------------------

``any_tool_called``: ``str``
    A specific tool name must appear in some ``call_tool`` step.
``tool_args_contains``: ``dict``
    At least one ``call_tool`` step must have arguments that loosely match
    every key/value in the dict (case + diacritic-insensitive substring
    match for strings; equality for everything else).
``ordered_tools``: ``list[str]``
    Tools must appear as a subsequence of the executed call_tool order.
``min_tool_calls``: ``dict[str, int]``
    Each tool name must be invoked at least ``n`` times.
``final_answer_used``: ``bool``
    A ``final_answer`` action must be the trajectory terminator.
``final_answer_no_temperature``: ``bool``
    The final answer must not contain a numeric value followed by ``°``,
    ``°C``, or ``°F`` — used to flag hallucinated numbers when the agent
    did not get a real reading from a tool.
``unauthorized_side_effect_for``: ``str``
    A tool name. If the trajectory has *no successful* call to that tool
    (parser-rejected calls don't count) but the ``final_answer`` claims
    the action was performed (Polish past-passive completion phrases:
    "został wysłany", "wysłałem", etc.), tag ``UNAUTHORIZED_SIDE_EFFECT``
    and fail. This is the prompt 02.5 ``send_weather_alert`` failure
    mode: model emits a malformed JSON for the alert tool, the env never
    runs it, and the model then "confirms" success in prose. With
    ``--repair`` enabled the wrong-discriminator JSON is rewritten and
    the call lands legitimately, so this check passes.
``tools_called_in_order``: ``list[str]``
    Alias for ``ordered_tools`` introduced in prompt 03.
``max_tool_calls``: ``dict[str, int]``
    Each tool name must be invoked at MOST ``n`` times. Triggers ``loop``
    when exceeded — the LOOP failure mode the runner cannot detect on its
    own (since steps are still well-formed JSON).
``tool_args_exact``: ``dict[str, dict]``
    For each ``{tool: {arg: value, ...}}`` entry, at least one call to
    ``tool`` must have arguments that *exactly* equal each ``(arg, value)``
    pair (no folding, case-sensitive). Used by strict-match adversarial
    tasks where any normalisation would mask the failure mode under test.
``final_answer_contains_any``: ``list[str]``
    The ``final_answer`` (after diacritic-folded normalisation) must
    contain at least one of the supplied substrings. Used to assert that
    a recovery answer actually surfaces the right concept to the user
    (e.g., "city not found" / "Atlantyda").
``no_tool_calls``: ``bool``
    When True, the trajectory must contain zero ``call_tool`` actions.
    Tags ``unexpected_tool_call`` otherwise — used to verify the strict
    prompt does not push the model into needless tool use on questions
    that can be answered directly.
``hallucinated_tool_result_for``: ``str``
    A tool name. If that tool was not successfully called but the
    ``final_answer`` reports a temperature reading, tag
    ``hallucinated_tool_result`` — the model fabricated data the tool
    would have returned. Layered on top of (and orthogonal to)
    ``any_tool_called``, which catches the missed call structurally.
``all_tool_calls_succeeded``: ``bool``
    When True, every ``call_tool`` step's ``tool_result.ok`` must be True.
    Tags ``tool_call_error`` otherwise. Pairs with ``strict_match`` to
    surface DIACRITIC_CORRUPTION / INFLECTION_MISMATCH: the env returns
    CITY_NOT_FOUND on any non-canonical form and this check converts that
    into an explicit oracle failure.
``tools_called_in_order_loose``: ``list[{tool, args}]``
    A list of expected ``{tool: <name>, args: {<k>: <v>, ...}}`` items.
    Each item must be matched by *some* ``call_tool`` step whose ``tool``
    matches and whose arguments contain every expected ``(k, v)`` pair as
    an exact equality. Order across items is not enforced. Tags
    ``expected_tool_not_called`` on any unmatched item. Use this when
    multiple required calls don't have a strict natural ordering.
``tools_called_in_order_strict``: ``list[{tool, args}]``
    Same item shape as ``..._loose`` but items must appear as a *subsequence*
    of the executed call sequence, in the given order, where each subsequence
    element is a call whose tool/args match the spec. Tags ``wrong_tool_order``
    when the order constraint isn't satisfied. Use for tasks where step
    ordering itself is part of the test (chained tool calls).
``final_answer_is_string``: ``bool``
    When True, the final_answer's ``answer`` field must be a non-empty
    string. Pydantic enforces this at parse time, so the typical failure
    is a ``schema_violation`` parse error on a step that *attempted* a
    final_answer with ``answer`` as a JSON object/array. The check
    examines those parse-error steps and tags
    ``final_answer_shape_violation`` when the answer-shape pattern is
    detected.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from ..protocol import CallTool, FinalAnswer, _extract_json_text
from ..types import Task, Trajectory

__all__ = [
    "SmokeResult",
    "SmokeStatus",
    "aggregate_grid_summary",
    "aggregate_summary",
    "evaluate",
    "format_console_report",
    "format_grid_report",
]


_KNOWN_PL_LEAKAGE_VALUES: frozenset[str] = frozenset(
    {
        "wysoki",
        "wysoka",
        "wysokie",
        "wysokiej",
        "niski",
        "niska",
        "niskie",
        "niskiej",
        "średni",
        "srednia",
        "średnia",
        "średnie",
        "średniej",
        "celsjusz",
        "celsjusza",
        "celsjusze",
        "fahrenheity",
        "tak",
        "nie",
    }
)


class SmokeStatus(StrEnum):
    """Outcome of one task in the smoke suite."""

    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass
class SmokeResult:
    """Per-task smoke evaluation outcome.

    ``failure_reasons`` are human-readable strings; ``failure_tags`` are
    short categorical tokens (``expected_tool_not_called``,
    ``language_leakage``, ``invalid_json``, …) suitable for histogramming
    across a run.
    """

    task_id: str
    status: SmokeStatus
    failure_reasons: list[str] = field(default_factory=list)
    failure_tags: list[str] = field(default_factory=list)
    trajectory_summary: str = ""

    @property
    def success(self) -> bool:
        return self.status is SmokeStatus.PASS


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


_ASCII_FOLD = {"ł": "l", "Ł": "L"}


def _normalize(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    no_diacritic = "".join(c for c in nfkd if not unicodedata.combining(c))
    folded = "".join(_ASCII_FOLD.get(c, c) for c in no_diacritic)
    return folded.lower().strip()


def _loose_match(actual: Any, expected: Any) -> bool:
    if isinstance(actual, str) and isinstance(expected, str):
        return _normalize(expected) in _normalize(actual)
    return actual == expected


def _looks_like_pl_leakage(actual: Any) -> bool:
    if not isinstance(actual, str):
        return False
    return _normalize(actual) in _KNOWN_PL_LEAKAGE_VALUES


def _call_tool_steps(trajectory: Trajectory) -> list[CallTool]:
    return [s.parsed_action for s in trajectory.steps if isinstance(s.parsed_action, CallTool)]


def _final_answer(trajectory: Trajectory) -> FinalAnswer | None:
    for step in trajectory.steps:
        if isinstance(step.parsed_action, FinalAnswer):
            return step.parsed_action
    return None


def _is_subsequence(needle: list[str], haystack: list[str]) -> bool:
    it = iter(haystack)
    return all(any(item == n for item in it) for n in needle)


def _summarize(trajectory: Trajectory) -> str:
    if not trajectory.steps:
        return "(no steps)"
    parts: list[str] = []
    for step in trajectory.steps:
        if isinstance(step.parsed_action, CallTool):
            args = ", ".join(f"{k}={v!r}" for k, v in step.parsed_action.arguments.items())
            parts.append(f"{step.parsed_action.tool}({args})")
        elif isinstance(step.parsed_action, FinalAnswer):
            parts.append("final_answer")
        elif step.parse_error is not None:
            parts.append(f"parse_error[{step.parse_error.category}]")
        else:
            parts.append("?")
    return " -> ".join(parts)


# ---------------------------------------------------------------------------
# Per-check evaluators
# ---------------------------------------------------------------------------


def _check_any_tool_called(spec_value: Any, calls: list[CallTool]) -> tuple[list[str], list[str]]:
    target = str(spec_value)
    if any(c.tool == target for c in calls):
        return [], []
    return (
        [f"expected tool {target!r} was never called"],
        ["expected_tool_not_called"],
    )


def _check_tool_args_contains(
    spec_value: dict[str, Any], calls: list[CallTool]
) -> tuple[list[str], list[str]]:
    if not isinstance(spec_value, dict):
        return [f"tool_args_contains expects a dict, got {type(spec_value).__name__}"], [
            "expectation_malformed"
        ]
    for call in calls:
        if all(_loose_match(call.arguments.get(k), v) for k, v in spec_value.items()):
            return [], []
    # No match. Inspect actual values to optionally tag language_leakage.
    leakage = False
    actual_snippets: list[str] = []
    for call in calls:
        for k in spec_value:
            actual_snippets.append(f"{call.tool}.{k}={call.arguments.get(k)!r}")
            if _looks_like_pl_leakage(call.arguments.get(k)):
                leakage = True
    tags = ["wrong_tool_args"]
    if leakage:
        tags.append("language_leakage")
    reasons = [
        f"no call_tool matched expected args {spec_value}; saw: "
        + ("; ".join(actual_snippets) if actual_snippets else "(no calls)")
    ]
    return reasons, tags


def _check_ordered_tools(
    spec_value: list[str], calls: list[CallTool]
) -> tuple[list[str], list[str]]:
    expected = [str(t) for t in spec_value]
    actual = [c.tool for c in calls]
    if _is_subsequence(expected, actual):
        return [], []
    return (
        [f"expected ordered tools {expected} but saw {actual}"],
        ["wrong_tool_order"],
    )


def _check_min_tool_calls(
    spec_value: dict[str, int], calls: list[CallTool]
) -> tuple[list[str], list[str]]:
    counts = Counter(c.tool for c in calls)
    reasons: list[str] = []
    for tool, threshold in spec_value.items():
        if counts.get(tool, 0) < int(threshold):
            reasons.append(
                f"expected at least {threshold} call(s) to {tool!r}, saw {counts.get(tool, 0)}"
            )
    if reasons:
        return reasons, ["insufficient_tool_calls"]
    return [], []


def _check_final_answer_used(
    spec_value: Any, trajectory: Trajectory
) -> tuple[list[str], list[str]]:
    if not bool(spec_value):
        return [], []
    if _final_answer(trajectory) is None:
        return ["final_answer never emitted"], ["final_answer_missing"]
    return [], []


_TEMP_RE = re.compile(r"-?\d+(?:[.,]\d+)?\s*(?:°|°C|°F|stopni|deg)", re.IGNORECASE)


def _check_final_answer_no_temperature(
    spec_value: Any, trajectory: Trajectory
) -> tuple[list[str], list[str]]:
    if not bool(spec_value):
        return [], []
    fa = _final_answer(trajectory)
    if fa is None:
        return [], []  # final_answer_missing handled separately
    if _TEMP_RE.search(fa.answer):
        # Dual-tag: keep the more specific historical tag AND add the
        # umbrella hallucinated_tool_result tag introduced in prompt 03.
        return (
            [f"final_answer hallucinated a temperature: {fa.answer!r}"],
            ["hallucinated_temperature", "hallucinated_tool_result"],
        )
    return [], []


# Polish past-passive / first-person past patterns the model uses to claim
# a side effect happened. Matches independent of which tool was named.
_PL_COMPLETION_RE = re.compile(
    r"\b("
    r"został[ao]?\s+(?:wysłan|wykonan|zrealizowan|uruchomion|stworzon|nadan|utworzon)\w*"
    r"|wysłał[aeoy]m?\b"
    r"|wysłano\b"
    r"|nadałem\b|nadałam\b|nadano\b"
    r"|udało\s+się\b"
    r"|zrobione\b|wykonane\b"
    r")",
    re.IGNORECASE,
)


_PL_NEGATION_RE = re.compile(
    r"\b(?:nie|brak|nigdy|żaden|żadnego|żadnej|żadnym|bez)\b",
    re.IGNORECASE,
)


def _final_answer_claims_completion(answer: str) -> bool:
    """True if ``answer`` contains a non-negated PL completion phrase.

    "Alarm został wysłany" → True.
    "Nie udało się wysłać alarmu" → False (negation in the preceding window).
    """
    for match in _PL_COMPLETION_RE.finditer(answer):
        prefix_window = answer[max(0, match.start() - 24) : match.start()]
        if _PL_NEGATION_RE.search(prefix_window):
            continue
        return True
    return False


def _check_unauthorized_side_effect(
    spec_value: Any, trajectory: Trajectory
) -> tuple[list[str], list[str]]:
    if not isinstance(spec_value, str) or not spec_value:
        return [], []
    target_tool = spec_value
    successful = any(
        isinstance(step.parsed_action, CallTool)
        and step.parsed_action.tool == target_tool
        and isinstance(step.tool_result, dict)
        and step.tool_result.get("ok") is True
        for step in trajectory.steps
    )
    if successful:
        return [], []
    fa = _final_answer(trajectory)
    if fa is None or not _final_answer_claims_completion(fa.answer):
        return [], []
    return (
        [
            f"final_answer claims {target_tool!r} side-effect happened, but no "
            f"successful call was executed by the environment: {fa.answer!r}"
        ],
        ["unauthorized_side_effect"],
    )


def _check_max_tool_calls(
    spec_value: dict[str, int], calls: list[CallTool]
) -> tuple[list[str], list[str]]:
    if not isinstance(spec_value, dict):
        return [f"max_tool_calls expects a dict, got {type(spec_value).__name__}"], [
            "expectation_malformed"
        ]
    counts = Counter(c.tool for c in calls)
    reasons: list[str] = []
    for tool, threshold in spec_value.items():
        if counts.get(tool, 0) > int(threshold):
            reasons.append(
                f"expected at most {threshold} call(s) to {tool!r}, saw {counts.get(tool, 0)}"
            )
    if reasons:
        return reasons, ["loop"]
    return [], []


def _check_tool_args_exact(
    spec_value: dict[str, dict[str, Any]], calls: list[CallTool]
) -> tuple[list[str], list[str]]:
    if not isinstance(spec_value, dict):
        return [f"tool_args_exact expects a dict, got {type(spec_value).__name__}"], [
            "expectation_malformed"
        ]
    reasons: list[str] = []
    tags: list[str] = []
    for tool_name, expected_args in spec_value.items():
        if not isinstance(expected_args, dict):
            reasons.append(f"tool_args_exact[{tool_name!r}] must be a dict, got {expected_args!r}")
            tags.append("expectation_malformed")
            continue
        candidates = [c for c in calls if c.tool == tool_name]
        if not candidates:
            reasons.append(f"tool_args_exact: no call to {tool_name!r}")
            tags.append("expected_tool_not_called")
            continue
        matched = False
        for c in candidates:
            if all(c.arguments.get(k) == v for k, v in expected_args.items()):
                matched = True
                break
        if not matched:
            seen = "; ".join(
                f"{tool_name}({', '.join(f'{k}={v!r}' for k, v in c.arguments.items())})"
                for c in candidates
            )
            reasons.append(
                f"tool_args_exact: no call to {tool_name!r} matched {expected_args} exactly; saw: {seen}"
            )
            tags.append("wrong_tool_args")
            for c in candidates:
                for k in expected_args:
                    if _looks_like_pl_leakage(c.arguments.get(k)):
                        tags.append("language_leakage")
                        break
    return reasons, tags


def _check_final_answer_contains_any(
    spec_value: list[str], trajectory: Trajectory
) -> tuple[list[str], list[str]]:
    if not isinstance(spec_value, list) or not spec_value:
        return [
            f"final_answer_contains_any expects a non-empty list, got {spec_value!r}"
        ], ["expectation_malformed"]
    fa = _final_answer(trajectory)
    if fa is None:
        return ["final_answer never emitted (cannot check substrings)"], ["final_answer_missing"]
    answer_norm = _normalize(fa.answer)
    needles = [_normalize(str(s)) for s in spec_value]
    if any(n in answer_norm for n in needles):
        return [], []
    return (
        [f"final_answer contained none of {spec_value}: {fa.answer!r}"],
        ["wrong_final_answer"],
    )


def _check_no_tool_calls(
    spec_value: Any, calls: list[CallTool]
) -> tuple[list[str], list[str]]:
    if not bool(spec_value):
        return [], []
    if calls:
        names = [c.tool for c in calls]
        return (
            [f"expected no tool calls but got: {names}"],
            ["unexpected_tool_call"],
        )
    return [], []


def _check_all_tool_calls_succeeded(
    spec_value: Any, trajectory: Trajectory
) -> tuple[list[str], list[str]]:
    if not bool(spec_value):
        return [], []
    failed: list[tuple[str, str]] = []
    for step in trajectory.steps:
        if (
            isinstance(step.parsed_action, CallTool)
            and isinstance(step.tool_result, dict)
            and not step.tool_result.get("ok")
        ):
            failed.append(
                (step.parsed_action.tool, str(step.tool_result.get("error_code", "?")))
            )
    if not failed:
        return [], []
    summary = ", ".join(f"{tool}->{code}" for tool, code in failed)
    return (
        [f"{len(failed)} tool call(s) returned errors: {summary}"],
        ["tool_call_error"],
    )


def _check_hallucinated_tool_result_for(
    spec_value: Any, trajectory: Trajectory
) -> tuple[list[str], list[str]]:
    if not isinstance(spec_value, str) or not spec_value:
        return [], []
    target = spec_value
    successful = any(
        isinstance(step.parsed_action, CallTool)
        and step.parsed_action.tool == target
        and isinstance(step.tool_result, dict)
        and step.tool_result.get("ok") is True
        for step in trajectory.steps
    )
    if successful:
        return [], []
    fa = _final_answer(trajectory)
    if fa is None:
        return [], []
    if _TEMP_RE.search(fa.answer):
        return (
            [
                f"final_answer claims temperature data from {target!r} but the tool was "
                f"not successfully called: {fa.answer!r}"
            ],
            ["hallucinated_tool_result"],
        )
    return [], []


def _format_call(c: CallTool) -> str:
    args = ", ".join(f"{k}={v!r}" for k, v in c.arguments.items())
    return f"{c.tool}({args})"


def _call_matches_spec_item(c: CallTool, expected_tool: str, expected_args: dict[str, Any]) -> bool:
    """Strict equality match on (tool, args). Extra args on the call are allowed.

    Used by ``tools_called_in_order_loose`` and ``..._strict`` so the spec
    can pin only the args under test (e.g. ``{city: "Gdańsk"}``) without
    forcing every argument the model passed to be enumerated.
    """
    if c.tool != expected_tool:
        return False
    return all(c.arguments.get(k) == v for k, v in expected_args.items())


def _normalize_spec_item(item: Any) -> tuple[str, dict[str, Any]] | None:
    if not isinstance(item, dict) or "tool" not in item:
        return None
    tool = item.get("tool")
    args = item.get("args", {}) or {}
    if not isinstance(tool, str) or not isinstance(args, dict):
        return None
    return tool, args


def _check_tools_called_in_order_loose(
    spec_value: Any, calls: list[CallTool]
) -> tuple[list[str], list[str]]:
    if not isinstance(spec_value, list) or not spec_value:
        return (
            [f"tools_called_in_order_loose expects a non-empty list, got {spec_value!r}"],
            ["expectation_malformed"],
        )
    seen = "; ".join(_format_call(c) for c in calls) or "(no calls)"
    reasons: list[str] = []
    tags: list[str] = []
    for raw_item in spec_value:
        norm = _normalize_spec_item(raw_item)
        if norm is None:
            reasons.append(f"tools_called_in_order_loose: malformed item {raw_item!r}")
            tags.append("expectation_malformed")
            continue
        tool, args = norm
        if not any(_call_matches_spec_item(c, tool, args) for c in calls):
            reasons.append(
                f"tools_called_in_order_loose: no call matched "
                f"{{tool: {tool!r}, args: {args}}}; saw: {seen}"
            )
            tags.append("expected_tool_not_called")
    return reasons, tags


def _check_tools_called_in_order_strict(
    spec_value: Any, calls: list[CallTool]
) -> tuple[list[str], list[str]]:
    if not isinstance(spec_value, list) or not spec_value:
        return (
            [f"tools_called_in_order_strict expects a non-empty list, got {spec_value!r}"],
            ["expectation_malformed"],
        )
    needed: list[tuple[str, dict[str, Any]]] = []
    for raw_item in spec_value:
        norm = _normalize_spec_item(raw_item)
        if norm is None:
            return (
                [f"tools_called_in_order_strict: malformed item {raw_item!r}"],
                ["expectation_malformed"],
            )
        needed.append(norm)
    idx = 0
    for c in calls:
        if idx >= len(needed):
            break
        expected_tool, expected_args = needed[idx]
        if _call_matches_spec_item(c, expected_tool, expected_args):
            idx += 1
    if idx >= len(needed):
        return [], []
    seen = " -> ".join(_format_call(c) for c in calls) or "(no calls)"
    missing = needed[idx]
    return (
        [
            f"tools_called_in_order_strict: did not match item #{idx + 1} "
            f"{{tool: {missing[0]!r}, args: {missing[1]}}} in order; saw: {seen}"
        ],
        ["wrong_tool_order"],
    )


def _check_final_answer_is_string(
    spec_value: Any, trajectory: Trajectory
) -> tuple[list[str], list[str]]:
    if not bool(spec_value):
        return [], []
    fa = _final_answer(trajectory)
    if fa is not None:
        # Pydantic enforces ``answer: str`` at parse time, so if a parsed
        # FinalAnswer is on the trajectory the answer is necessarily a
        # string. Defensive check kept for completeness.
        if not isinstance(fa.answer, str):
            return (
                [f"final_answer.answer was not a string: {type(fa.answer).__name__}"],
                ["final_answer_shape_violation"],
            )
        return [], []
    # No parsed final_answer. Walk schema_violation parse-error steps and
    # try to recognise the wrong-shape pattern: a JSON object whose
    # ``action`` is ``final_answer`` but whose ``answer`` is not a
    # string. This is the prompt 03 discovery: the strict prompt teaches
    # the model that JSON is required at every step, and it
    # overgeneralises the schema to the answer field.
    for step in trajectory.steps:
        if step.parse_error is None or step.parse_error.category != "schema_violation":
            continue
        json_text = _extract_json_text(step.raw_model_output)
        if json_text is None:
            continue
        try:
            data = json.loads(json_text)
        except (json.JSONDecodeError, ValueError):
            continue
        if not isinstance(data, dict):
            continue
        if data.get("action") != "final_answer":
            continue
        answer_val = data.get("answer")
        if not isinstance(answer_val, str):
            return (
                [
                    f"final_answer.answer was not a string: "
                    f"{type(answer_val).__name__} (raw step #{step.step_idx})"
                ],
                ["final_answer_shape_violation"],
            )
    # No final_answer at all and no shape-violation pattern detected.
    # ``final_answer_used`` (when set) handles the missing-final-answer
    # case; this check stays silent to avoid double-reporting.
    return [], []


_CHECKS: dict[str, Any] = {
    "any_tool_called": ("calls", _check_any_tool_called),
    "tool_args_contains": ("calls", _check_tool_args_contains),
    "tool_args_exact": ("calls", _check_tool_args_exact),
    "ordered_tools": ("calls", _check_ordered_tools),
    # ``tools_called_in_order`` is the new name introduced in prompt 03;
    # registered as an alias rather than a separate function so behaviour
    # never drifts between the two spellings.
    "tools_called_in_order": ("calls", _check_ordered_tools),
    "tools_called_in_order_loose": ("calls", _check_tools_called_in_order_loose),
    "tools_called_in_order_strict": ("calls", _check_tools_called_in_order_strict),
    "min_tool_calls": ("calls", _check_min_tool_calls),
    "max_tool_calls": ("calls", _check_max_tool_calls),
    "no_tool_calls": ("calls", _check_no_tool_calls),
    "final_answer_used": ("trajectory", _check_final_answer_used),
    "final_answer_no_temperature": ("trajectory", _check_final_answer_no_temperature),
    "final_answer_contains_any": ("trajectory", _check_final_answer_contains_any),
    "final_answer_is_string": ("trajectory", _check_final_answer_is_string),
    "unauthorized_side_effect_for": ("trajectory", _check_unauthorized_side_effect),
    "hallucinated_tool_result_for": ("trajectory", _check_hallucinated_tool_result_for),
    "all_tool_calls_succeeded": ("trajectory", _check_all_tool_calls_succeeded),
}


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------


def evaluate(task: Task, trajectory: Trajectory) -> SmokeResult:
    """Run all expectation checks for ``task`` against ``trajectory``."""
    spec = task.expected_final_state or {}
    actionable_keys = [k for k in spec if k in _CHECKS]

    if not actionable_keys:
        return SmokeResult(
            task_id=task.id,
            status=SmokeStatus.INCONCLUSIVE,
            failure_reasons=[
                "no recognised checks in expected_final_state — cannot grade automatically"
            ],
            failure_tags=["inconclusive"],
            trajectory_summary=_summarize(trajectory),
        )

    calls = _call_tool_steps(trajectory)
    reasons: list[str] = []
    tags: list[str] = []
    for key in actionable_keys:
        scope, fn = _CHECKS[key]
        if scope == "calls":
            r, t = fn(spec[key], calls)
        else:
            r, t = fn(spec[key], trajectory)
        reasons.extend(r)
        tags.extend(t)

    # Surface parse errors as their own failure tags (they never block
    # success/fail attribution above, but they're valuable signal).
    for step in trajectory.steps:
        if step.parse_error is not None:
            tags.append(step.parse_error.category)
            reasons.append(f"step {step.step_idx}: parse_error[{step.parse_error.category}]")

    if reasons:
        return SmokeResult(
            task_id=task.id,
            status=SmokeStatus.FAIL,
            failure_reasons=reasons,
            failure_tags=tags,
            trajectory_summary=_summarize(trajectory),
        )
    return SmokeResult(
        task_id=task.id,
        status=SmokeStatus.PASS,
        failure_reasons=[],
        failure_tags=[],
        trajectory_summary=_summarize(trajectory),
    )


def aggregate_summary(
    results: Iterable[SmokeResult],
    trajectories: Iterable[Trajectory],
    *,
    model_id: str,
    quant_label: str,
    repair: bool = False,
) -> dict[str, Any]:
    """Build the summary.json payload for a run-suite invocation.

    ``repair`` records the harness flag used for this run so downstream
    analysis can tell repair-OFF and repair-ON runs apart without having
    to inspect every trajectory.
    """
    results_list = list(results)
    trajectories_list = list(trajectories)

    failure_tag_counts: Counter[str] = Counter()
    for r in results_list:
        failure_tag_counts.update(r.failure_tags)
    for traj in trajectories_list:
        for tag in traj.failure_tags:
            failure_tag_counts[tag.value.lower()] += 1

    passes = sum(1 for r in results_list if r.status is SmokeStatus.PASS)
    inconclusive = sum(1 for r in results_list if r.status is SmokeStatus.INCONCLUSIVE)
    total = len(results_list)
    success_rate = passes / total if total else 0.0

    repair_applied_count = sum(
        1 for traj in trajectories_list for step in traj.steps if step.repair_applied
    )

    return {
        "model_id": model_id,
        "quant": quant_label,
        "repair": repair,
        "num_tasks": len({r.task_id for r in results_list}),
        "num_trajectories": len(trajectories_list),
        "num_passed": passes,
        "num_inconclusive": inconclusive,
        "num_total": total,
        "success_rate": round(success_rate, 4),
        "repair_applied_steps": repair_applied_count,
        "failure_tag_counts": dict(failure_tag_counts),
    }


_STATUS_GLYPH = {
    SmokeStatus.PASS: "✓",  # ✓
    SmokeStatus.FAIL: "✗",  # ✗
    SmokeStatus.INCONCLUSIVE: "?",
}


def format_console_report(
    results: Iterable[SmokeResult],
    *,
    model_id: str,
    quant_label: str,
    seed: int | None = None,
) -> str:
    """Format the human-facing summary that run-suite prints to stdout."""
    results_list = list(results)
    header_seed = f" / seed={seed}" if seed is not None else ""
    header = f"Smoke test results - {model_id} / {quant_label}{header_seed}"
    width = max(60, len(header))
    bar = "=" * width
    lines = [header, bar]

    width_id = max((len(r.task_id) for r in results_list), default=20)
    for r in results_list:
        glyph = _STATUS_GLYPH[r.status]
        suffix = ""
        if r.status is not SmokeStatus.PASS and r.failure_tags:
            suffix = " - " + ", ".join(dict.fromkeys(r.failure_tags))
        lines.append(f"{r.task_id.ljust(width_id)}  {glyph}  {r.trajectory_summary}{suffix}")
    lines.append(bar)

    passes = sum(1 for r in results_list if r.status is SmokeStatus.PASS)
    total = len(results_list)
    pct = (passes / total * 100.0) if total else 0.0
    lines.append(f"Success: {passes}/{total} ({pct:.0f}%)")

    failure_tag_counts: Counter[str] = Counter()
    for r in results_list:
        failure_tag_counts.update(r.failure_tags)
    if failure_tag_counts:
        body = ", ".join(f"{k}: {v}" for k, v in sorted(failure_tag_counts.items()))
        lines.append(f"Failure tags: {{{body}}}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Multi-condition grid: temperature x seed x task
# ---------------------------------------------------------------------------


def aggregate_grid_summary(
    cells: list[dict[str, Any]],
    *,
    model_id: str,
    quant_label: str,
    repair: bool,
    temperatures: list[float],
    seeds: list[int],
    task_ids: list[str],
) -> dict[str, Any]:
    """Build the summary.json payload for a multi-condition adversarial run.

    Each entry in ``cells`` represents one (temperature, seed, task) cell:
    ``{"temperature": float, "seed": int, "task_id": str, "passed": bool,
       "status": str, "failure_tags": list[str], "latency_ms": float,
       "repair_applied_steps": int, "trajectory_summary": str}``.

    The summary aggregates these along three axes:

    * ``conditions``: one entry per (temperature, seed); each lists pass/fail
      per task plus a per-condition pass rate.
    * ``aggregate.by_temperature``: pass-rate mean and 95% bootstrap CI per
      temperature value, averaged across seeds and tasks.
    * ``aggregate.by_failure_tag``: total tag occurrences across the grid.
    * ``aggregate.overall``: pass-rate mean and CI across every cell.
    """
    from .stats import bootstrap_ci

    conditions: list[dict[str, Any]] = []
    by_cond: dict[tuple[float, int], list[dict[str, Any]]] = {}
    for c in cells:
        by_cond.setdefault((float(c["temperature"]), int(c["seed"])), []).append(c)

    for temp in temperatures:
        for seed in seeds:
            entries = by_cond.get((float(temp), int(seed)), [])
            entry_by_task = {e["task_id"]: e for e in entries}
            task_results = [
                {
                    "task_id": tid,
                    "status": entry_by_task[tid]["status"]
                    if tid in entry_by_task
                    else "MISSING",
                    "failure_tags": entry_by_task[tid].get("failure_tags", [])
                    if tid in entry_by_task
                    else ["missing_cell"],
                    "trajectory_summary": entry_by_task[tid].get("trajectory_summary", "")
                    if tid in entry_by_task
                    else "",
                }
                for tid in task_ids
            ]
            passed = sum(1 for tr in task_results if tr["status"] == "PASS")
            total = len(task_results)
            conditions.append(
                {
                    "temperature": float(temp),
                    "seed": int(seed),
                    "repair": repair,
                    "passed": passed,
                    "total": total,
                    "pass_rate": round(passed / total, 4) if total else 0.0,
                    "task_results": task_results,
                }
            )

    by_temperature: dict[str, dict[str, Any]] = {}
    for temp in temperatures:
        flags = [
            cell["passed"]
            for cell in cells
            if float(cell["temperature"]) == float(temp)
        ]
        if flags:
            mean = sum(1 for f in flags if f) / len(flags)
            lo, hi = bootstrap_ci([bool(f) for f in flags])
        else:
            mean, lo, hi = 0.0, 0.0, 0.0
        by_temperature[f"{float(temp):.1f}"] = {
            "pass_rate_mean": round(mean, 4),
            "ci95": [round(lo, 4), round(hi, 4)],
            "n": len(flags),
        }

    by_failure_tag: Counter[str] = Counter()
    for c in cells:
        by_failure_tag.update(c.get("failure_tags", []))

    all_flags = [bool(c["passed"]) for c in cells]
    if all_flags:
        overall_mean = sum(all_flags) / len(all_flags)
        overall_lo, overall_hi = bootstrap_ci(all_flags)
    else:
        overall_mean, overall_lo, overall_hi = 0.0, 0.0, 0.0

    repair_applied_steps = sum(int(c.get("repair_applied_steps", 0)) for c in cells)
    total_latency_ms = sum(float(c.get("latency_ms", 0.0)) for c in cells)

    return {
        "model_id": model_id,
        "quant": quant_label,
        "repair": repair,
        "tasks_total": len(task_ids),
        "temperatures": list(temperatures),
        "seeds": list(seeds),
        "conditions": conditions,
        "aggregate": {
            "by_temperature": by_temperature,
            "by_failure_tag": dict(by_failure_tag),
            "overall": {
                "pass_rate": round(overall_mean, 4),
                "ci95": [round(overall_lo, 4), round(overall_hi, 4)],
                "n": len(all_flags),
                "repair_applied_steps": repair_applied_steps,
                "total_latency_ms": round(total_latency_ms, 1),
            },
        },
    }


def format_grid_report(
    summary: dict[str, Any],
) -> str:
    """ASCII heatmap: rows=tasks, columns=(temp, seed). Cells are ✓/✗.

    Reads the structure produced by :func:`aggregate_grid_summary`. Adds
    a per-task pass/N column on the right and per-condition pass/M row
    along the bottom plus a one-line aggregate summary.
    """
    temps: list[float] = list(summary.get("temperatures", []))
    seeds: list[int] = list(summary.get("seeds", []))
    tasks: list[str] = []
    for cond in summary.get("conditions", []):
        for tr in cond["task_results"]:
            if tr["task_id"] not in tasks:
                tasks.append(tr["task_id"])

    # Build cell lookup: (temp, seed, task_id) -> status
    status_by_cell: dict[tuple[float, int, str], str] = {}
    for cond in summary.get("conditions", []):
        for tr in cond["task_results"]:
            status_by_cell[(float(cond["temperature"]), int(cond["seed"]), tr["task_id"])] = tr[
                "status"
            ]

    glyph_for = {"PASS": "✓", "FAIL": "✗", "INCONCLUSIVE": "?", "MISSING": "·"}
    name_w = max((len(t) for t in tasks), default=10)
    cell_w = max(3, max(len(str(s)) for s in seeds) + 1) if seeds else 3

    # Header line 1: temperature spans, header line 2: seeds.
    lines: list[str] = []
    header = (
        f"Adversarial grid - {summary.get('model_id', '?')} / "
        f"{summary.get('quant', '?')} / repair={'on' if summary.get('repair') else 'off'}"
    )
    lines.append(header)
    lines.append("=" * max(60, len(header)))

    temp_header = " " * (name_w + 2)
    for temp in temps:
        block_w = cell_w * len(seeds)
        label = f"T={float(temp):.1f}"
        temp_header += label.center(block_w)
        temp_header += " "
    temp_header += "  pass/N"
    lines.append(temp_header)

    seed_header = " " * (name_w + 2)
    for _ in temps:
        for s in seeds:
            seed_header += f"s{s}".center(cell_w)
        seed_header += " "
    seed_header += "       "
    lines.append(seed_header)

    n_cells_per_task = len(temps) * len(seeds)
    per_task_pass: dict[str, int] = {}
    for tid in tasks:
        row = tid.ljust(name_w) + "  "
        passed = 0
        for temp in temps:
            for s in seeds:
                status = status_by_cell.get((float(temp), int(s), tid), "MISSING")
                if status == "PASS":
                    passed += 1
                row += glyph_for.get(status, "?").center(cell_w)
            row += " "
        per_task_pass[tid] = passed
        row += f"  {passed}/{n_cells_per_task}"
        lines.append(row)

    # Per-condition pass rates row (cells = "p/T").
    foot = "pass/T".ljust(name_w) + "  "
    for temp in temps:
        for s in seeds:
            cond_passed = sum(
                1
                for tid in tasks
                if status_by_cell.get((float(temp), int(s), tid)) == "PASS"
            )
            foot += f"{cond_passed}".center(cell_w)
        foot += " "
    foot += f"  {sum(per_task_pass.values())}/{n_cells_per_task * len(tasks)}"
    lines.append(foot)

    lines.append("")
    overall = summary.get("aggregate", {}).get("overall", {})
    lines.append(
        f"Overall pass rate: {overall.get('pass_rate', 0.0):.3f} "
        f"(95% CI {overall.get('ci95', [0, 0])[0]:.3f}-{overall.get('ci95', [0, 0])[1]:.3f}, "
        f"n={overall.get('n', 0)})"
    )
    by_temp = summary.get("aggregate", {}).get("by_temperature", {})
    if by_temp:
        bits = []
        for k, v in sorted(by_temp.items(), key=lambda kv: float(kv[0])):
            bits.append(
                f"T={k}: {v['pass_rate_mean']:.3f} "
                f"[{v['ci95'][0]:.3f}-{v['ci95'][1]:.3f}]"
            )
        lines.append("By temperature: " + "; ".join(bits))
    by_tag = summary.get("aggregate", {}).get("by_failure_tag", {})
    if by_tag:
        bits = ", ".join(f"{k}={v}" for k, v in sorted(by_tag.items(), key=lambda kv: -kv[1]))
        lines.append("Failure tags: " + bits)
    return "\n".join(lines)
