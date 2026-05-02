"""System-prompt builders.

A *single* prompt template per language describes the universal action
protocol and renders the per-task tool schemas. The template is deliberately
minimal: we want the model's natural propensities to surface, not to engineer
them away. Mitigations (PL tool descriptions, validator-driven repair) live
behind a separate flag and are added in later prompts.
"""

from __future__ import annotations

import json
from typing import Any, Literal

__all__ = ["build_system_prompt"]


PromptLanguage = Literal["pl", "en"]


def build_system_prompt(
    available_tools: list[dict[str, Any]],
    language: PromptLanguage = "pl",
    max_steps: int = 8,
) -> str:
    """Render the system prompt for one language and one tool inventory.

    The output never contains markdown fences (the model is told not to emit
    them either) and stays under ~800 tokens for typical 5-tool inventories,
    so the long-context budget is reserved for trajectory state.
    """
    if language == "pl":
        return _build_pl(available_tools, max_steps)
    if language == "en":
        return _build_en(available_tools, max_steps)
    raise ValueError(f"unsupported language: {language!r}")


def _render_tools(available_tools: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for tool in available_tools:
        name = tool.get("name", "<unnamed>")
        description = tool.get("description", "")
        parameters = tool.get("parameters", {})
        lines.append(f"- name: {name}")
        if description:
            lines.append(f"  description: {description}")
        if parameters:
            lines.append(f"  parameters: {json.dumps(parameters, ensure_ascii=False)}")
    return "\n".join(lines)


def _build_pl(available_tools: list[dict[str, Any]], max_steps: int) -> str:
    tools_block = _render_tools(available_tools)
    return (
        "Jesteś agentem korzystającym z narzędzi. W każdej turze WYBIERZ DOKŁADNIE "
        "JEDNĄ akcję i zwróć ją jako pojedynczy obiekt JSON. Nie pisz prozy, nie "
        "używaj bloków kodu (```), nie dodawaj wyjaśnień.\n"
        "\n"
        'Format akcji (dyskryminator: pole "action"):\n'
        "\n"
        "(1) Wywołanie narzędzia:\n"
        '{"action": "call_tool", "tool": "<nazwa>", "arguments": {...}}\n'
        "\n"
        "(2) Odpowiedź końcowa:\n"
        '{"action": "final_answer", "answer": "<treść>"}\n'
        "\n"
        "Dostępne narzędzia:\n"
        f"{tools_block}\n"
        "\n"
        "Zasady:\n"
        "- Wypisz dokładnie jeden obiekt JSON na turę. Bez prozy, bez bloków ```.\n"
        "- Po wywołaniu narzędzia otrzymasz wynik jako wiadomość "
        '<tool_result tool="...">{...}</tool_result>.\n'
        "- Gdy masz wystarczająco informacji, użyj final_answer.\n"
        f"- Limit kroków na to zadanie: {max_steps}.\n"
    )


def _build_en(available_tools: list[dict[str, Any]], max_steps: int) -> str:
    tools_block = _render_tools(available_tools)
    return (
        "You are a tool-using agent. On every turn CHOOSE EXACTLY ONE action and "
        "return it as a single JSON object. Do not write prose, do not use code "
        "fences (```), do not add explanations.\n"
        "\n"
        'Action format (discriminator: "action" field):\n'
        "\n"
        "(1) Call a tool:\n"
        '{"action": "call_tool", "tool": "<name>", "arguments": {...}}\n'
        "\n"
        "(2) Final answer:\n"
        '{"action": "final_answer", "answer": "<text>"}\n'
        "\n"
        "Available tools:\n"
        f"{tools_block}\n"
        "\n"
        "Rules:\n"
        "- Emit exactly one JSON object per turn. No prose, no ``` fences.\n"
        "- After calling a tool you will receive its result as "
        '<tool_result tool="...">{...}</tool_result>.\n'
        "- When you have enough information, use final_answer.\n"
        f"- Step budget for this task: {max_steps}.\n"
    )
