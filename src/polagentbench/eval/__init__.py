"""Evaluators for PolAgentBench trajectories.

The smoke evaluator (``smoke``) is intentionally permissive — it answers the
single question "does the agent broadly do the right thing on this task?".
Strict per-category evaluators land in later prompts.
"""

from __future__ import annotations

from .smoke import SmokeResult, SmokeStatus, aggregate_summary, evaluate, format_console_report

__all__ = [
    "SmokeResult",
    "SmokeStatus",
    "aggregate_summary",
    "evaluate",
    "format_console_report",
]
