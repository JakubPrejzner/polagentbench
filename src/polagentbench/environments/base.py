"""Abstract environment interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

__all__ = ["Environment"]


class Environment(ABC):
    """Stateful tool execution environment.

    The runner calls :meth:`execute_tool` for each agent ``call_tool`` action,
    receives an observation dict, and threads it back to the model. Concrete
    environments are responsible for any state mutations that real-world tools
    would induce (sending an alert, creating an invoice, updating a calendar).

    Observations follow a standard shape so the runner / evaluator can treat
    them uniformly:

    * On success: ``{"ok": True, "result": <tool-specific payload>}``.
    * On error: ``{"ok": False, "error": <human message>, "error_code": <category>}``.

    The ``error_code`` vocabulary is per-environment but should be stable
    across runs so failure-mode statistics are comparable.
    """

    @abstractmethod
    def reset(self, initial_state: dict[str, Any]) -> None:
        """Reset the environment to a fresh state.

        Called once at the start of every task run. ``initial_state`` is loaded
        by the runner from :attr:`Task.initial_state_path` and may be empty
        for stateless environments.
        """

    @abstractmethod
    def execute_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a single tool call and return an observation dict.

        Implementations must never raise on bad input — model-driven
        misuse is the data we care about. Convert exceptions into structured
        error observations with an ``error_code`` so the trajectory record
        captures *what* went wrong.
        """

    @abstractmethod
    def current_state(self) -> dict[str, Any]:
        """Return a JSON-serialisable snapshot of the current environment state.

        Used by the runner to populate :attr:`TrajectoryStep.state_after`
        after each step, and to populate :attr:`Trajectory.final_state` at
        the end of the run.
        """

    @abstractmethod
    def available_tool_names(self) -> list[str]:
        """Return the set of tool names this environment recognises.

        Useful for sanity-checking task YAMLs against environments and for
        the CLI to print a quick "what's installed" summary.
        """
