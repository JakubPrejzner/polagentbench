# Prompt 03.5 — suite cleanup, mid-difficulty tasks, re-run

Bielik-Minitron-7B-v3.0-Instruct Q8_0 GGUF on a fresh Vast 4090 instance.
Two passes (repair OFF, repair ON) over the new 13-task adversarial suite
(15 task IDs after the 4→{4a,4b} and 9→{9a,9b} splits) at temperatures
{0.0, 0.3, 0.7} and seeds {42, 43, 44}. 135 trajectories per pass, 270
total.

---

## 1. Did the splits work as designed?

**adv_004a (clean diacritic probe, single city, strict_match)**
Pass A 9/9, Pass B 9/9. Bielik handles `Świnoujście` correctly under
strict-match. Confirms what the original adv_004 hinted at (the
diacritic itself is not the failure mode) but with a clean signal —
this task now isolates `DIACRITIC_CORRUPTION` as designed.

**adv_004b (two cities + final_answer_is_string oracle)**
Pass A 0/9, Pass B 0/9. Every single cell fails with the same shape —
`{"action":"final_answer","answer":{"Świnoujście":{"temperature_c":8.0,...},"Żory":{...}}}`
— and the new `final_answer_shape_violation` failure tag fires 8 times
in each pass (two parse-error steps per trajectory in some cells, hence
8 not 9). The split worked: the answer-shape failure mode now has its
own clean probe.

**adv_009a (pure arithmetic over Zakopane vs Tatry)**
Pass A 6/9, Pass B 6/9. **Lands in the diagnostic band.** Failures are
genuine arithmetic errors at higher temperatures: T=0.3 s42 → "3°C",
T=0.7 s42 → "17°C" (model converted both temps to Fahrenheit and lost
the plot), T=0.7 s44 → "3°C". At T=0.0 the model emits raw `<tool_result
tool='get_weather' city='Zakopane'><temperature_c>2.0</temperature_c>`
template tags in the answer (prompt-template leakage, separate concern)
but still computes `2.0 - (-5.0) = 7.0` correctly so the oracle passes.

**adv_009b (clean wrong-discriminator probe)**
Pass A 9/9, Pass B 9/9. **Too easy.** Bielik passes this even without
repair — the wrong-discriminator pattern doesn't fire on a single,
unconditional `send_weather_alert` request. To make this discriminating
we'd need to surround the alert with another tool call or stick it
behind a small reasoning step where the model is more likely to elide
the `action: call_tool` discriminator.

## 2. Do the new mid-difficulty tasks land in 30-70%?

| task    | Pass A | Pass B | failure pattern (when it fires) |
|---------|--------|--------|---------------------------------|
| adv_011 | 9/9    | 9/9    | (none — Polish numeral parsing handled fine) |
| adv_012 | 9/9    | 9/9    | (none — negation handled, alert correctly skipped) |
| adv_013 | 7/9    | 7/9    | T=0.3 s42 + T=0.7 s42: strict-order violation on three-tool chain |

So **one** of the three new tasks (adv_013) lands in the diagnostic band.
adv_011 and adv_012 are too easy — Bielik 7B at Q8 is comfortably
capable of "pięć → 5" and of refraining from a tool call when told
"NIE wysyłaj." Combined with adv_009a's 6/9, the suite has **two
diagnostic-band tasks** as of this run.

## 3. Updated full-suite stats

### 3.1 Heatmap (Pass A, repair OFF)

```
            T=0.0     T=0.3     T=0.7     pass/N
          s42s43s44 s42s43s44 s42s43s44
adv_001    ✓  ✓  ✓   ✓  ✓  ✓   ✓  ✓  ✓    9/9
adv_002    ✓  ✓  ✓   ✓  ✓  ✓   ✓  ✓  ✓    9/9
adv_003    ✓  ✓  ✓   ✓  ✓  ✓   ✓  ✓  ✓    9/9
adv_004a   ✓  ✓  ✓   ✓  ✓  ✓   ✓  ✓  ✓    9/9
adv_004b   ✗  ✗  ✗   ✗  ✗  ✗   ✗  ✗  ✗    0/9
adv_005    ✓  ✓  ✓   ✓  ✓  ✓   ✓  ✓  ✓    9/9
adv_006    ✓  ✓  ✓   ✓  ✓  ✓   ✓  ✓  ✓    9/9
adv_007    ✓  ✓  ✓   ✓  ✓  ✓   ✓  ✓  ✓    9/9
adv_008    ✓  ✓  ✓   ✓  ✓  ✓   ✓  ✓  ✓    9/9
adv_009a   ✓  ✓  ✓   ✗  ✓  ✗   ✓  ✓  ✗    6/9
adv_009b   ✓  ✓  ✓   ✓  ✓  ✓   ✓  ✓  ✓    9/9
adv_010    ✓  ✓  ✓   ✓  ✓  ✓   ✓  ✓  ✓    9/9
adv_011    ✓  ✓  ✓   ✓  ✓  ✓   ✓  ✓  ✓    9/9
adv_012    ✓  ✓  ✓   ✓  ✓  ✓   ✓  ✓  ✓    9/9
adv_013    ✓  ✓  ✓   ✗  ✓  ✓   ✗  ✓  ✓    7/9
pass/T     14 14 14  12 14 13  13 14 13   121/135
```

### 3.2 Pass B (repair ON) — same shape

Cell-for-cell identical to Pass A. 121/135 = 0.896 in both. Heatmap
omitted; the only delta is in the failure-tag histogram and in
`repair_applied_steps` (0 → 6).

### 3.3 Overall pass rate (with bootstrap CIs)

| run                | pass rate | 95% CI            | n   |
|--------------------|-----------|-------------------|-----|
| original Pass A    | 0.800     | [0.711, 0.878]    | 90  |
| original Pass B    | 0.833     | [0.756, 0.911]    | 90  |
| **v2 Pass A**      | **0.896** | **[0.844, 0.941]**| 135 |
| **v2 Pass B**      | **0.896** | **[0.844, 0.941]**| 135 |

The aggregate moves up because the original 0/9 floor tasks were one of
the things being measured; splitting them removes the entangled failure
mode (4b still floors but 4a no longer does, and 9a now passes 6/9).

By temperature (v2):
- T=0.0: 0.933 (CI 0.844-1.000)
- T=0.3: 0.867 (CI 0.756-0.956)
- T=0.7: 0.889 (CI 0.778-0.978)

The mild dip at T=0.3/0.7 (vs T=0.0) tracks the arithmetic noise on
adv_009a + the order violations on adv_013.

### 3.4 Failure tag distribution

| tag                              | Pass A | Pass B | Δ   |
|----------------------------------|--------|--------|-----|
| final_answer_missing             | 10     | 12     | +2  |
| schema_violation                 | 10     | 10     |  0  |
| **final_answer_shape_violation** | **8**  | **8**  |  0  |
| wrong_final_answer               | 3      | 1      | -2  |
| unknown_action                   | 3      | 1      | -2  |

`unknown_action` and `wrong_final_answer` each drop by 2 in Pass B,
consistent with repair landing 6 wrong-discriminator calls (mostly on
adv_009a's `convert_temperature` calls) — but those 6 lands don't flip
any cell pass/fail because the underlying arithmetic was already
broken. `final_answer_missing` ticks up by 2 because the now-landed
`convert_temperature` calls eat additional steps before the trajectory
hits `max_steps`.

The new `final_answer_shape_violation` tag fires 8× in each pass, all
on adv_004b. That's the same answer-shape JSON-object pattern in every
cell — the wrong-shape violation is rock-solid deterministic at this
seed/temp grid.

### 3.5 McNemar (paired, cell-level, A vs B)

```
n_total=135, n_disc=0  (n10=0 A pass→B fail, n01=0 A fail→B pass)
p_value=1.0000
```

The two passes are cell-identical. Repair fires (6 steps over 2 cells)
but doesn't flip any pass/fail outcome because the cells where it fires
are already failing for an arithmetic-not-protocol reason. **The
prompt-03 finding (3 fixes, 0 regressions, p=0.25) was specific to the
original 9-conditional-alert structure; with the cleaner adv_009b
probe, repair has nothing left to fix.**

## 4. Gradient assessment

Distribution of per-task pass counts (Pass A, 9 cells per task):

| bucket               | count |
|----------------------|-------|
| 0/9 floor            | 1 (adv_004b) |
| 1-2/9 hard           | 0 |
| **3-7/9 diagnostic** | **2 (adv_009a 6/9, adv_013 7/9)** |
| 8/9 near-ceiling     | 0 |
| 9/9 ceiling          | 12 |

So we now have **two** diagnostic-band tasks where prompt 03 had zero,
plus one clean answer-shape probe at the floor. That's a 4-point
gradient (0, 6, 7, 9) instead of the original 2-point (0, 9). Enough
for Qwen to land somewhere differentiable on at least three tasks.

The suite is **usable** for Qwen comparison but **not yet ideal** —
12/15 tasks still hit ceiling at Bielik-7B-Q8. If Qwen also hits 9/9
on those 12, the discriminating signal lives entirely on
{004b, 009a, 013}, which is statistical thin ice.

## 5. Recommendations for prompt 04 (Qwen baseline)

### Should drop or further harden

- **adv_011 (Polish numerals)**: ceiling-bound at this model size. Polish
  numeral parsing for single small integers is solved; either drop or
  upgrade to compound numerals like "trzysta dwadzieścia pięć" (325) or
  ordinal forms like "co czwarty dzień" with implicit conversion.
- **adv_012 (negation)**: 9/9. Bielik handles "if NIE … NIE …" cleanly.
  Either drop or rewrite with deeper nesting ("send the alert *unless*
  the temperature is below freezing AND it isn't raining").
- **adv_009b (wrong-discriminator probe)**: 9/9. Repair fires zero times
  here — the failure mode it's meant to surface doesn't surface in this
  isolated form on Bielik. Move the alert behind a get_weather → reason
  → alert chain so the model has more steps to drift.

### New mid-difficulty candidates worth designing

The two failure modes that *do* fire intermittently on Bielik 7B Q8 are:

1. **Arithmetic over signed temperatures with negative numbers** —
   adv_009a fails 3/9. Build 1-2 more variants: pressure differences,
   day-over-day forecast comparisons, signed-difference questions where
   the model must produce a Polish wording for a negative result.
2. **Strict-order violations on chained tool calls** — adv_013 fails
   2/9. Build a 4-tool variant or one where the second tool's args
   depend non-trivially on the first tool's output (so a misordered
   call returns an env error rather than just a wrong order).

Specific failure modes still not surfacing in the v2 suite:
- `LANGUAGE_LEAKAGE` — fired in prompt 02.5 smoke 003 but not in any v2
  cell. Strict prompt is genuinely effective. Don't chase it for now.
- `IDENTIFIER_CORRUPTION` — never fired. The strict-match adv_003 +
  adv_004a both pass 9/9. Bielik's identifier handling is robust enough
  that this isn't a measurable axis for this model size.

### Suite design takeaway

Bielik-Minitron-7B at Q8 is **near-ceiling** on most strict-prompt
PL_EN tool-use tasks. To get a useful Qwen-vs-Bielik comparison the
diagnostic-band fraction needs to grow from 2/15 to ~5/15. Two paths:
(a) make existing ceiling-tasks harder (compound numerals, deeper
nesting, longer chains); (b) add a Q4 quantization to Bielik in the
same comparison so we expose the actual quant-degradation gradient
that's the paper's thesis. (b) is prompt 05 territory but might be
worth pulling forward if the Qwen-only run leaves us with too few
discriminating tasks.

## 6. Compute / latency

| run     | total wall-clock | n   | per-traj |
|---------|------------------|-----|----------|
| v2 A    | 273.7s           | 135 | 2.03s    |
| v2 B    | 285.5s           | 135 | 2.12s    |

~9-10 minutes per pass on a 4090 with Q8. A full Bielik+Qwen run at this
suite shape (4 conditions × 135 cells = 540 trajectories) ≈ 18-20 min
of GPU time, modest. Adding Q4-Bielik makes it 6 conditions / ~30 min.
Vast spend remains negligible.

## 7. Status

- All 200 local tests pass.
- Both Vast runs landed cleanly.
- Results pulled to `results/adv_run_003_v2_no_repair/` and
  `results/adv_run_004_v2_repair/`.
- 4 atomic commits on main:
  1. `chore(lint): drop redundant int() casts; tidy import block in test_eval_stats`
  2. `feat(types,eval): tools_called_in_order_loose/strict + final_answer_is_string oracles`
  3. `feat(tasks): split adv_004/009 + add 3 mid-difficulty adversarial tasks`
  4. `test(suite): cover new oracles + adapt CLI/load tests for 13-task suite`
- Vast instance left warm; can be stopped at user's discretion.
