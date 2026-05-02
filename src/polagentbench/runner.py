"""Abstract runner interface.

Concrete implementations (notably ``LlamaCppRunner`` for GGUF models served
via ``llama-cpp-python``) are added in a later prompt. This module exists so
that downstream code — orchestration, evaluators, tests — can already depend
on a stable interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .types import Task, Trajectory

__all__ = ["ModelRunner"]


class ModelRunner(ABC):
    """Abstract base for any model that can attempt a :class:`Task`.

    Implementations are responsible for:

    * Rendering the task prompt and tool schemas into the model's input format
      (we use a single universal action protocol; see
      :mod:`polagentbench.protocol`).
    * Driving the loop of model output → parse → tool execution → next step,
      respecting :attr:`Task.max_steps`.
    * Accumulating a :class:`Trajectory` with one :class:`TrajectoryStep` per
      model turn.

    Concrete subclasses (e.g. ``LlamaCppRunner``) live in later prompts; this
    module deliberately ships only the contract.
    """

    @abstractmethod
    def run_task(self, task: Task, seed: int) -> Trajectory:
        """Execute ``task`` end-to-end and return the full trajectory.

        Implementations must not raise on model misbehaviour: parse errors,
        invalid tool calls, and step-budget exhaustion are all expected
        outcomes that should be recorded on the :class:`Trajectory`.
        """

    @abstractmethod
    def model_id(self) -> str:
        """Return a stable identifier for the underlying model.

        Used as a column key in result tables. Should include the model
        family and size, e.g. ``"bielik-11b-v3.0-instruct"``.
        """

    @abstractmethod
    def quant_label(self) -> str:
        """Return the quantization label for this runner.

        Conventional values: ``"BF16"``, ``"Q8_0"``, ``"Q4_K_M"``, ``"Q2_K"``.
        """
