"""System-prompt builders.

Each language gets exactly one prompt: a strict baseline that hammers the
"every turn must be a JSON object" rule. Smoke runs against the previous
permissive prompt (prompt 02.5) showed instruction-tuned Bielik reverting
to Polish prose for the *terminal* step in 4 of 5 tasks — emitting JSON
for tool calls, then a free-form natural reply once it had the data. The
strict prompt below adds three things proven to fix that pattern in
similar tool-using setups: a hard rule in capitals, an explicit two-turn
walkthrough showing JSON-after-tool-result, and an anti-pattern list.

We deliberately do not soften the prompt (no "please", no examples that
omit the discriminator). The goal of the benchmark is to measure where
quantization breaks agents, not where weak prompting does. Mitigations
that change this baseline (PL-translated descriptions, validator-driven
repair) get their own flags.
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
    them either). Polish is the smoke-test baseline; English mirrors the
    structure but isn't yet language-tuned (no English smoke runs in this
    project state).
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
        "KAŻDA TWOJA ODPOWIEDŹ MUSI BYĆ JEDNYM OBIEKTEM JSON. ZAWSZE.\n"
        "NIGDY nie odpowiadaj prozą. NIGDY nie wyjaśniaj. NIGDY nie używaj markdown.\n"
        "Nawet jeśli masz już wszystkie dane do odpowiedzi - zapakuj odpowiedź w JSON\n"
        'z action="final_answer".\n'
        "\n"
        "Jesteś agentem korzystającym z narzędzi. Format akcji "
        '(dyskryminator: pole "action"):\n'
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
        "Przykład pełnej trajektorii:\n"
        "\n"
        'User: "Jaka jest pogoda w Krakowie?"\n'
        "Asystent (tura 1):\n"
        '{"action": "call_tool", "tool": "get_weather", "arguments": {"city": "Kraków"}}\n'
        "\n"
        'User: <tool_result tool="get_weather">'
        '{"ok": true, "result": {"temperature_c": 7.5, "condition": "rain"}}'
        "</tool_result>\n"
        "\n"
        "Asystent (tura 2 - finalna):\n"
        '{"action": "final_answer", "answer": "W Krakowie jest 7.5°C i pada deszcz."}\n'
        "\n"
        "UWAGA: Tura 2 to NADAL JSON, mimo że masz już dane. NIE odpowiadaj prozą.\n"
        "\n"
        f"Limit kroków: {max_steps}.\n"
        "\n"
        "ZABRONIONE odpowiedzi:\n"
        '- "Pogoda w Krakowie to 7.5°C." (proza, brak JSON)\n'
        '- "```json\\n{...}\\n```" (markdown wrapper)\n'
        '- "Odpowiedź: {...}" (prefiks tekstowy)\n'
        '- {"answer": "..."} (brak pola action)\n'
        "\n"
        'DOZWOLONE: tylko czysty obiekt JSON z polem "action".\n'
    )


def _build_en(available_tools: list[dict[str, Any]], max_steps: int) -> str:
    tools_block = _render_tools(available_tools)
    return (
        "EVERY RESPONSE MUST BE A SINGLE JSON OBJECT. ALWAYS.\n"
        "NEVER reply in prose. NEVER explain. NEVER use markdown fences.\n"
        "Even when you already have the data to answer - wrap the answer in JSON\n"
        'with action="final_answer".\n'
        "\n"
        'You are a tool-using agent. Action format (discriminator: "action" field):\n'
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
        "Example trajectory:\n"
        "\n"
        'User: "What is the weather in Krakow?"\n'
        "Assistant (turn 1):\n"
        '{"action": "call_tool", "tool": "get_weather", "arguments": {"city": "Kraków"}}\n'
        "\n"
        'User: <tool_result tool="get_weather">'
        '{"ok": true, "result": {"temperature_c": 7.5, "condition": "rain"}}'
        "</tool_result>\n"
        "\n"
        "Assistant (turn 2 - final):\n"
        '{"action": "final_answer", "answer": "Krakow is 7.5°C with rain."}\n'
        "\n"
        "NOTE: Turn 2 is STILL JSON even though you have the data. Do NOT reply in prose.\n"
        "\n"
        f"Step budget: {max_steps}.\n"
        "\n"
        "FORBIDDEN responses:\n"
        '- "It is 7.5°C in Krakow." (prose, no JSON)\n'
        '- "```json\\n{...}\\n```" (markdown wrapper)\n'
        '- "Answer: {...}" (text prefix)\n'
        '- {"answer": "..."} (missing action field)\n'
        "\n"
        'ALLOWED: only a clean JSON object with an "action" field.\n'
    )
