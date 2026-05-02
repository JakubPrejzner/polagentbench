"""Core types shared across the PolAgentBench harness.

These models describe tasks (the input to a run), trajectories (the recorded
output of a run), and the categorical labels used to slice results: task
category, interface variant, and post-hoc failure tags.

All pydantic models are configured with ``extra="forbid"`` so that typos in
task YAMLs or runner outputs surface as validation errors rather than silently
ignored fields.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .protocol import Action, ParseError

__all__ = [
    "FailureTag",
    "InterfaceVariant",
    "Task",
    "TaskCategory",
    "Trajectory",
    "TrajectoryStep",
]


class InterfaceVariant(StrEnum):
    """Language combinations exercised by a task.

    * ``EN_EN``: English user prompt, English tool schema. Baseline.
    * ``PL_EN``: Polish user prompt, English tool schema (the realistic case).
    * ``PL_EN_PL_DESC``: Polish prompt, English schema, but tool ``description``
      strings are translated to Polish — a low-cost mitigation we want to
      measure.
    """

    EN_EN = "EN_EN"
    PL_EN = "PL_EN"
    PL_EN_PL_DESC = "PL_EN_PL_DESC"


class TaskCategory(StrEnum):
    """High-level task family. Determines which evaluator is applied."""

    TOOL_SELECTION = "TOOL_SELECTION"
    STATEFUL = "STATEFUL"
    CONSTRAINT = "CONSTRAINT"
    RECOVERY = "RECOVERY"


class FailureTag(StrEnum):
    """Post-hoc labels applied to failed trajectories.

    The enum is fixed up-front so that downstream analysis code can rely on a
    closed vocabulary, but actual auto-tagging logic lives in the evaluator
    (added in a later prompt).
    """

    SCHEMA_FRACTURE = "SCHEMA_FRACTURE"
    LANGUAGE_LEAKAGE = "LANGUAGE_LEAKAGE"
    INFLECTION_MISMATCH = "INFLECTION_MISMATCH"
    DIACRITIC_CORRUPTION = "DIACRITIC_CORRUPTION"
    IDENTIFIER_CORRUPTION = "IDENTIFIER_CORRUPTION"
    DATE_NORMALIZATION = "DATE_NORMALIZATION"
    UNAUTHORIZED_SIDE_EFFECT = "UNAUTHORIZED_SIDE_EFFECT"
    HALLUCINATED_TOOL_RESULT = "HALLUCINATED_TOOL_RESULT"
    RECOVERY_COLLAPSE = "RECOVERY_COLLAPSE"
    LOOP = "LOOP"
    TIMEOUT = "TIMEOUT"
    INVALID_TOOL_CALL = "INVALID_TOOL_CALL"
    WRONG_TOOL = "WRONG_TOOL"
    WRONG_ARGUMENT = "WRONG_ARGUMENT"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"


class Task(BaseModel):
    """A single benchmark task.

    Tool schemas are kept as raw dicts (rather than a typed model) because the
    benchmark intentionally exposes models to JSON-Schema-shaped tool
    descriptions identical to what real agent stacks pass through.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, description="Unique task identifier.")
    category: TaskCategory
    environment: str = Field(
        min_length=1,
        description="Name of the Environment registered with the runner that this task targets.",
    )
    language_variant: InterfaceVariant
    prompt: str = Field(min_length=1, description="User-facing prompt shown to the model.")
    available_tools: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Tool schemas exposed to the model. Free-form JSON-Schema-shaped dicts.",
    )
    initial_state_path: Path = Field(
        description="Path (relative to the task file) to the JSON file holding initial env state."
    )
    expected_final_state: dict[str, Any] = Field(
        default_factory=dict,
        description="Subset of the env state that must hold for the task to be considered solved.",
    )
    max_steps: int = Field(default=8, gt=0, description="Maximum action steps before timeout.")
    constraints: list[str] = Field(
        default_factory=list,
        description="Free-form natural-language constraints. Used by the constraint evaluator.",
    )
    source_path: Path | None = Field(
        default=None,
        description=(
            "Absolute path to the YAML this task was loaded from. Populated by load_task; "
            "left None when the task is constructed in memory. Used to resolve "
            "initial_state_path."
        ),
    )
    strict_match: bool = Field(
        default=False,
        description=(
            "If True, the environment must use exact-match identifier resolution: "
            "no diacritic folding, no inflection folding, no normalisation. Used to "
            "force DIACRITIC_CORRUPTION / INFLECTION_MISMATCH failure modes to surface "
            "rather than be silently corrected by the environment."
        ),
    )
    hardcoded_state: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Optional environment-specific state overrides applied at reset(). "
            "Namespaced by category for forward-compatibility, e.g. "
            "{'cities': {'Poznań': {'condition': 'rain'}}}. Concrete environments "
            "decide which namespaces they honour."
        ),
    )


class TrajectoryStep(BaseModel):
    """One step in a model's interaction with the environment.

    A step may end in a successful action, a parse error, or a tool error;
    those are recorded distinctly so downstream evaluators can attribute
    failures correctly.
    """

    model_config = ConfigDict(extra="forbid")

    step_idx: int = Field(ge=0, description="Zero-based index of this step in the trajectory.")
    raw_model_output: str = Field(
        description=(
            "Text actually fed to parse_action for this step. When repair is enabled "
            "and fired, this is the *post-repair* text; the original is preserved "
            "in ``raw_model_output_pre_repair``."
        )
    )
    parsed_action: Action | None = Field(
        default=None,
        description="Parsed action when parsing succeeded; otherwise None.",
    )
    parse_error: ParseError | None = Field(
        default=None,
        description="Structured parse error when the model output could not be parsed.",
    )
    tool_result: dict[str, Any] | None = Field(
        default=None,
        description="Result returned by the tool, if any was invoked.",
    )
    state_after: dict[str, Any] | None = Field(
        default=None,
        description="Environment state snapshot taken after this step.",
    )
    latency_ms: float = Field(
        ge=0.0,
        description="Wall-clock latency of this step (model + tool execution), in milliseconds.",
    )
    repair_applied: bool = Field(
        default=False,
        description=(
            "True if attempt_repair fired on this step's raw output and the "
            "repaired text replaced the original before parsing."
        ),
    )
    raw_model_output_pre_repair: str | None = Field(
        default=None,
        description=(
            "Original verbatim model output, populated only when repair_applied "
            "is True. Lets analysis distinguish 'agent emitted this directly' "
            "from 'agent emitted X but the runner rewrote it'."
        ),
    )


class Trajectory(BaseModel):
    """A complete record of one model attempting one task."""

    model_config = ConfigDict(extra="forbid")

    task_id: str
    model_id: str
    quant: str = Field(description="Quantization label, e.g. 'BF16', 'Q4_K_M', 'Q2_K'.")
    interface_variant: InterfaceVariant
    seed: int
    steps: list[TrajectoryStep] = Field(default_factory=list)
    final_state: dict[str, Any] | None = Field(
        default=None,
        description="Final environment state at end of trajectory, if available.",
    )
    success: bool = False
    failure_tags: list[FailureTag] = Field(
        default_factory=list,
        description="Post-hoc failure tags. Empty on success.",
    )
    total_latency_ms: float = Field(ge=0.0, default=0.0)
    total_tokens: int = Field(ge=0, default=0)
