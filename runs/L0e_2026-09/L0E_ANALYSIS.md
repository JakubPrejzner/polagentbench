# L0e rerun analysis (2026-09-07)

## 0. Oracle replay and environment control

| cell | repair | L0e pass | L0 control pass | L0 release pass | control raw identical /10 | control tokens equal /10 | control verdict equal /10 |
|---|---|---|---|---|---|---|---|
| 11B Q8_0 | no_repair | 1/10 | 0/10 | 0/10 | 10 | 10 | 10 |
| 11B Q8_0 | repair | 1/10 | 0/10 | 0/10 | 10 | 10 | 10 |
| 11B Q4_K_M | no_repair | 0/10 | 0/10 | 0/10 | 10 | 10 | 10 |
| 11B Q4_K_M | repair | 0/10 | 0/10 | 0/10 | 10 | 10 | 10 |
| 7B Q8_0 | no_repair | 0/10 | 0/10 | 0/10 | 10 | 10 | 10 |
| 7B Q8_0 | repair | 0/10 | 0/10 | 0/10 | 10 | 10 | 10 |
| 7B Q4_K_M | no_repair | 0/10 | 0/10 | 0/10 | 10 | 10 | 10 |
| 7B Q4_K_M | repair | 0/10 | 0/10 | 0/10 | 10 | 10 | 10 |

Oracle replay: every verdict and tag set equals run.log and summary.json in all 16 runs (else this script stops). Control trajectories identical in raw_model_output to release_data: **80/80**.

## 1. L0 (release, 2026-07-29) vs L0e (explicit prohibition, 2026-09-07), paired per instance

| cell | repair | L0 pass | L0e pass | n11 | n10 (L0 only) | n01 (L0e only) | n00 | instances L0e-only | L0e trajectories with any tool call | L0e tag counts |
|---|---|---|---|---|---|---|---|---|---|---|
| 11B Q8_0 | no_repair | 0/10 | 1/10 | 0 | 0 | 1 | 9 | g | 0/10 | wrong_final_answer 9 |
| 11B Q8_0 | repair | 0/10 | 1/10 | 0 | 0 | 1 | 9 | g | 0/10 | wrong_final_answer 9 |
| 11B Q4_K_M | no_repair | 0/10 | 0/10 | 0 | 0 | 0 | 10 | - | 0/10 | final_answer_missing 6, no_json_found 9, unknown_action 9, wrong_final_answer 1 |
| 11B Q4_K_M | repair | 0/10 | 0/10 | 0 | 0 | 0 | 10 | - | 0/10 | final_answer_missing 6, no_json_found 9, unknown_action 9, wrong_final_answer 1 |
| 7B Q8_0 | no_repair | 0/10 | 0/10 | 0 | 0 | 0 | 10 | - | 10/10 | final_answer_missing 10, schema_violation 10, unexpected_tool_call 10 |
| 7B Q8_0 | repair | 0/10 | 0/10 | 0 | 0 | 0 | 10 | - | 10/10 | final_answer_missing 10, schema_violation 10, unexpected_tool_call 10 |
| 7B Q4_K_M | no_repair | 0/10 | 0/10 | 0 | 0 | 0 | 10 | - | 0/10 | final_answer_missing 5, schema_violation 1, unknown_action 4, wrong_final_answer 5 |
| 7B Q4_K_M | repair | 0/10 | 0/10 | 0 | 0 | 0 | 10 | - | 4/10 | final_answer_missing 1, schema_violation 1, unexpected_tool_call 4, unknown_action 4, wrong_final_answer 9 |

Reference, L0 release tag counts and tool calls: see per_task_ladder46.csv; L0 control (same box, original prompt) tag counts:

- 11B Q8_0 no_repair: control tool calls 10/10, tags {'no_json_found': 1, 'unexpected_tool_call': 10, 'wrong_final_answer': 5}
- 11B Q8_0 repair: control tool calls 10/10, tags {'no_json_found': 1, 'unexpected_tool_call': 10, 'wrong_final_answer': 5}
- 11B Q4_K_M no_repair: control tool calls 10/10, tags {'final_answer_missing': 1, 'invalid_json': 1, 'schema_violation': 1, 'unexpected_tool_call': 10, 'wrong_final_answer': 5}
- 11B Q4_K_M repair: control tool calls 10/10, tags {'final_answer_missing': 1, 'invalid_json': 1, 'schema_violation': 1, 'unexpected_tool_call': 10, 'wrong_final_answer': 5}
- 7B Q8_0 no_repair: control tool calls 0/10, tags {'final_answer_missing': 9, 'invalid_json': 1, 'schema_violation': 3, 'unknown_action': 10, 'wrong_final_answer': 1}
- 7B Q8_0 repair: control tool calls 10/10, tags {'final_answer_missing': 4, 'schema_violation': 3, 'unexpected_tool_call': 10, 'unknown_action': 9, 'wrong_final_answer': 6}
- 7B Q4_K_M no_repair: control tool calls 4/10, tags {'final_answer_missing': 7, 'unexpected_tool_call': 4, 'unknown_action': 10}
- 7B Q4_K_M repair: control tool calls 10/10, tags {'final_answer_missing': 1, 'schema_violation': 1, 'unexpected_tool_call': 10, 'unknown_action': 6, 'wrong_final_answer': 7}

Content diagnosis of L0e answers (what the model computed), per cell:

| cell | repair | pass | averaged all four readings | right Celsius mean, wrong Fahrenheit | other value | no final answer |
|---|---|---|---|---|---|---|
| 11B Q8_0 | no_repair | 1 | 8 | 0 | 1 | 0 |
| 11B Q8_0 | repair | 1 | 8 | 0 | 1 | 0 |
| 11B Q4_K_M | no_repair | 0 | 1 | 0 | 3 | 6 |
| 11B Q4_K_M | repair | 0 | 1 | 0 | 3 | 6 |
| 7B Q8_0 | no_repair | 0 | 0 | 0 | 0 | 10 |
| 7B Q8_0 | repair | 0 | 0 | 0 | 0 | 10 |
| 7B Q4_K_M | no_repair | 0 | 4 | 0 | 1 | 5 |
| 7B Q4_K_M | repair | 0 | 4 | 0 | 5 | 1 |

L0e final answers (repair = off), instance: answer:

- **11B Q8_0**: a [F, gold 46.4] 'Średnia temperatura z drugiego i czwartego dnia wynosi 7.75°C, co odpo'; b [F, gold 48.2] 'Średnia temperatura z drugiego i czwartego dnia wynosi 8.75°C, co odpo'; c [F, gold 45.5] 'Średnia temperatura z drugiego i czwartego dnia wynosi 7.25°C, co odpo'; d [F, gold 47.3] 'Średnia temperatura z drugiego i czwartego dnia wynosi 8.25°C, co odpo'; e [F, gold 46.4] 'Średnia temperatura z drugiego i czwartego dnia wynosi 7.75°C, co odpo'; f [F, gold 45.5] 'Średnia temperatura z drugiego i czwartego dnia wynosi 7.25°C, co odpo'; g [P, gold 35.6] 'Średnia temperatura z drugiego i czwartego dnia wynosi 2°C, co w przel'; h [F, gold 41.9] 'Średnia temperatura z drugiego i czwartego dnia wynosi 5.75°C, co odpo'; i [F, gold 42.8] 'Średnia temperatura z drugiego i czwartego dnia wynosi 5.75°C, co odpo'; j [F, gold 43.7] 'Średnia temperatura z drugiego i czwartego dnia wynosi 6.25°C, co odpo'
- **11B Q4_K_M**: a [F, gold 46.4] '46.4'; b [F, gold 48.2] '48.2'; c [F, gold 45.5] '<no final answer>'; d [F, gold 47.3] '<no final answer>'; e [F, gold 46.4] '46.4'; f [F, gold 45.5] '<no final answer>'; g [F, gold 35.6] '<no final answer>'; h [F, gold 41.9] '<no final answer>'; i [F, gold 42.8] '<no final answer>'; j [F, gold 43.7] 'Średnia temperatura z drugiego i czwartego dnia to 6.25°C, co w przeli'
- **7B Q8_0**: a [F, gold 46.4] '<no final answer>'; b [F, gold 48.2] '<no final answer>'; c [F, gold 45.5] '<no final answer>'; d [F, gold 47.3] '<no final answer>'; e [F, gold 46.4] '<no final answer>'; f [F, gold 45.5] '<no final answer>'; g [F, gold 35.6] '<no final answer>'; h [F, gold 41.9] '<no final answer>'; i [F, gold 42.8] '<no final answer>'; j [F, gold 43.7] '<no final answer>'
- **7B Q4_K_M**: a [F, gold 46.4] 'Średnia temperatura z drugiego i czwartego dnia wynosi 7.75°C, co odpo'; b [F, gold 48.2] '<no final answer>'; c [F, gold 45.5] 'Średnia temperatura z drugiego i czwartego dnia wynosi 7.25°C, co odpo'; d [F, gold 47.3] 'Średnia temperatura z drugiego i czwartego dnia wynosi 8.75°C, co odpo'; e [F, gold 46.4] 'Średnia temperatura z drugiego i czwartego dnia wynosi 7.75°C, co odpo'; f [F, gold 45.5] 'Średnia temperatura z drugiego i czwartego dnia wynosi 7.25°C, co odpo'; g [F, gold 35.6] '<no final answer>'; h [F, gold 41.9] '<no final answer>'; i [F, gold 42.8] '<no final answer>'; j [F, gold 43.7] '<no final answer>'

## 2. Finding 3 with L0e as the baseline (exact two-sided McNemar, instance-paired)


### repair = off

| model | precision | contrast | rate | L0e | rung | n11 | n10 | n01 | n00 | p |
|---|---|---|---|---|---|---|---|---|---|---|
| 11B | Q8_0 | L0e vs L3N (n=10) | strict | 1/10 | 2/10 | 0 | 1 | 2 | 7 | 1 |
| 11B | Q8_0 | L0e vs L3N (n=10) | corrected | 1/10 | 9/10 | 1 | 0 | 8 | 1 | 0.007812 |
| 11B | Q8_0 | L0e vs L3T (n=6) | strict | 0/6 | 6/6 | 0 | 0 | 6 | 0 | 0.03125 |
| 11B | Q4_K_M | L0e vs L3N (n=10) | strict | 0/10 | 0/10 | 0 | 0 | 0 | 10 | 1 |
| 11B | Q4_K_M | L0e vs L3N (n=10) | corrected | 0/10 | 4/10 | 0 | 0 | 4 | 6 | 0.125 |
| 11B | Q4_K_M | L0e vs L3T (n=6) | strict | 0/6 | 0/6 | 0 | 0 | 0 | 6 | 1 |
| 7B | Q8_0 | L0e vs L3N (n=10) | strict | 0/10 | 0/10 | 0 | 0 | 0 | 10 | 1 |
| 7B | Q8_0 | L0e vs L3N (n=10) | corrected | 0/10 | 7/10 | 0 | 0 | 7 | 3 | 0.01562 |
| 7B | Q8_0 | L0e vs L3T (n=6) | strict | 0/6 | 0/6 | 0 | 0 | 0 | 6 | 1 |
| 7B | Q4_K_M | L0e vs L3N (n=10) | strict | 0/10 | 1/10 | 0 | 0 | 1 | 9 | 1 |
| 7B | Q4_K_M | L0e vs L3N (n=10) | corrected | 0/10 | 3/10 | 0 | 0 | 3 | 7 | 0.25 |
| 7B | Q4_K_M | L0e vs L3T (n=6) | strict | 0/6 | 0/6 | 0 | 0 | 0 | 6 | 1 |

### repair = on

| model | precision | contrast | rate | L0e | rung | n11 | n10 | n01 | n00 | p |
|---|---|---|---|---|---|---|---|---|---|---|
| 11B | Q8_0 | L0e vs L3N (n=10) | strict | 1/10 | 2/10 | 0 | 1 | 2 | 7 | 1 |
| 11B | Q8_0 | L0e vs L3T (n=6) | strict | 0/6 | 6/6 | 0 | 0 | 6 | 0 | 0.03125 |
| 11B | Q4_K_M | L0e vs L3N (n=10) | strict | 0/10 | 0/10 | 0 | 0 | 0 | 10 | 1 |
| 11B | Q4_K_M | L0e vs L3T (n=6) | strict | 0/6 | 4/6 | 0 | 0 | 4 | 2 | 0.125 |
| 7B | Q8_0 | L0e vs L3N (n=10) | strict | 0/10 | 0/10 | 0 | 0 | 0 | 10 | 1 |
| 7B | Q8_0 | L0e vs L3T (n=6) | strict | 0/6 | 0/6 | 0 | 0 | 0 | 6 | 1 |
| 7B | Q4_K_M | L0e vs L3N (n=10) | strict | 0/10 | 1/10 | 0 | 0 | 1 | 9 | 1 |
| 7B | Q4_K_M | L0e vs L3T (n=6) | strict | 0/6 | 3/6 | 0 | 0 | 3 | 3 | 0.25 |

### Holm within the repair = off family (12 tests)

| test | raw p | Holm p | significant at 0.05 |
|---|---|---|---|
| 11B Q8_0 L0e vs L3N strict | 1 | 1 | no |
| 11B Q8_0 L0e vs L3N corrected | 0.007812 | 0.09375 | no |
| 11B Q8_0 L0e vs L3T strict | 0.03125 | 0.3125 | no |
| 11B Q4_K_M L0e vs L3N strict | 1 | 1 | no |
| 11B Q4_K_M L0e vs L3N corrected | 0.125 | 1 | no |
| 11B Q4_K_M L0e vs L3T strict | 1 | 1 | no |
| 7B Q8_0 L0e vs L3N strict | 1 | 1 | no |
| 7B Q8_0 L0e vs L3N corrected | 0.01562 | 0.1719 | no |
| 7B Q8_0 L0e vs L3T strict | 1 | 1 | no |
| 7B Q4_K_M L0e vs L3N strict | 1 | 1 | no |
| 7B Q4_K_M L0e vs L3N corrected | 0.25 | 1 | no |
| 7B Q4_K_M L0e vs L3T strict | 1 | 1 | no |
