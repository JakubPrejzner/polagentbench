"""Tool execution environments for PolAgentBench.

Each environment implements :class:`Environment` and exposes a fixed set of
tools that the agent can invoke. The runner does not know about specific
environments — it looks them up by name from a registry passed at
construction time, keyed on :attr:`polagentbench.types.Task.environment`.
"""

from __future__ import annotations

from .base import Environment
from .weather import WeatherEnvironment

__all__ = ["Environment", "WeatherEnvironment"]
