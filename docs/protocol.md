# Universal Action Protocol

PolAgentBench evaluates tool-using LLM agents across model families and
quantization levels. To make those comparisons sound, every model — Bielik,
Qwen, anything else — must speak the **same** action language. This document
specifies that language.

## Why a universal protocol (and not native tool calling)

Modern instruction-tuned LLMs ship with vendor-specific tool-calling formats:
OpenAI uses `tool_calls` arrays, Anthropic embeds `<tool_use>` XML, llama.cpp
varies by template. If we used each model's native format, we would be
comparing **prompt-engineering quality across families** as much as model
behaviour, which contaminates the variable we care about (quantization ×
language interface).

Instead, every model is asked to emit a small JSON object via the system
prompt, and the harness parses that JSON the same way for every model. This:

- Removes a confound from the experimental design.
- Lets us measure "schema fracture" cleanly: the number of times the model
  fails to emit valid protocol JSON is itself a metric.
- Keeps the parser simple, fast, and stdlib-only on the hot path.

## Action types

There are exactly two action types. Models must emit one per turn.

### `call_tool`

Invoke a named tool with structured arguments.

```json
{
  "action": "call_tool",
  "tool": "search_customer",
  "arguments": {"city": "Łódź", "name": "Anna Nowak"}
}
```

Field rules:

| Field       | Type           | Required | Notes                                      |
|-------------|----------------|----------|--------------------------------------------|
| `action`    | `"call_tool"`  | yes      | Discriminator literal                      |
| `tool`      | string         | yes      | Non-empty                                  |
| `arguments` | object         | no       | Defaults to `{}`. Must be a JSON object.   |

### `final_answer`

Terminate the trajectory and return a natural-language reply.

```json
{
  "action": "final_answer",
  "answer": "Klient nie istnieje w bazie."
}
```

Field rules:

| Field    | Type             | Required | Notes        |
|----------|------------------|----------|--------------|
| `action` | `"final_answer"` | yes      | Discriminator |
| `answer` | string           | yes      | Non-empty    |

### Strictness

The pydantic models use `extra="forbid"`: any unexpected field causes a
`schema_violation`. This is intentional — quantized models often hallucinate
adjacent fields (`"function"` instead of `"tool"`, `"params"` instead of
`"arguments"`) and we want those failures to be visible in the metrics rather
than silently coerced.

## Parsing model output

The harness calls `polagentbench.protocol.parse_action(text)`, which always
returns an `ActionResult` and never raises. The parser is tolerant of common
formatting noise:

1. **Markdown code fences.** Many instruction-tuned models wrap JSON in
   ```` ```json ... ``` ```` or plain ```` ``` ... ``` ````. The parser
   detects fenced blocks first.
2. **Surrounding prose.** If no fence is present the parser scans for the
   first balanced `{...}` substring, correctly skipping braces inside JSON
   string literals.

If a candidate substring is found it is parsed with stdlib `json`, then the
resulting dict is fed through a pydantic discriminated-union `TypeAdapter`.

## Error categories

`ParseError.category` is one of:

| Category            | When it fires                                                |
|---------------------|---------------------------------------------------------------|
| `no_json_found`     | No `{...}` substring (fenced or otherwise) could be located. |
| `invalid_json`      | A candidate was found but `json.loads` failed (or the top-level value is not an object). |
| `unknown_action`    | JSON parsed but `action` is not `"call_tool"` or `"final_answer"`. |
| `schema_violation`  | `action` is recognised but a required field is missing, malformed, or an extra field is present. |

These categories map directly to the failure tags reported in the benchmark
output, so the same vocabulary flows from low-level parsing all the way to the
final results table.

## Performance note

The parser is on the hot path (one call per model step, summed across runs ×
seeds × variants). It uses only stdlib `json` plus pydantic v2's
`TypeAdapter`, no external regex engines beyond stdlib `re`, and never
allocates beyond what's needed for the candidate substring. Don't add
dependencies here without thinking through cost.
