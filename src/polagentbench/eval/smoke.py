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
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from ..protocol import CallTool, FinalAnswer
from ..types import Task, Trajectory

__all__ = [
    "SmokeResult",
    "SmokeStatus",
    "aggregate_summary",
    "evaluate",
    "format_console_report",
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
        return (
            [f"final_answer hallucinated a temperature: {fa.answer!r}"],
            ["hallucinated_temperature"],
        )
    return [], []


_CHECKS: dict[str, Any] = {
    "any_tool_called": ("calls", _check_any_tool_called),
    "tool_args_contains": ("calls", _check_tool_args_contains),
    "ordered_tools": ("calls", _check_ordered_tools),
    "min_tool_calls": ("calls", _check_min_tool_calls),
    "final_answer_used": ("trajectory", _check_final_answer_used),
    "final_answer_no_temperature": ("trajectory", _check_final_answer_no_temperature),
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
) -> dict[str, Any]:
    """Build the summary.json payload for a run-suite invocation."""
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

    return {
        "model_id": model_id,
        "quant": quant_label,
        "num_tasks": len({r.task_id for r in results_list}),
        "num_trajectories": len(trajectories_list),
        "num_passed": passes,
        "num_inconclusive": inconclusive,
        "num_total": total,
        "success_rate": round(success_rate, 4),
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
