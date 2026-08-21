"""Rigorous oracle for EVERY arith task in the hard tier (KROK 1 audit + KROK 3 validation).

For each arith task (final_answer_contains_any present AND the chain either converts
to Fahrenheit or pulls a forecast) we:
  * dry-replay the strict tool chain in a live WeatherEnvironment to recover the
    source Celsius value (forecast mean, or single get_weather reading);
  * pick the averaging scheme (full forecast mean vs day2/day4 mean) whose EXACT
    F string is accepted by the golden — that is the scheme the task encodes;
  * build THREE real trajectories and run the project's real evaluate():
      exact    — full-precision mean -> must PASS
      rounded  — round(mean, 1) before C->F (the mine simulation) -> should PASS
      negative — correct tool calls but final answer reports Celsius -> must FAIL
  * flag MINE = exact PASS but rounded FAIL; and WHOLE = °F is an integer
    multiple of 5 (substring hazard: model writes "50" which lacks "50.0").

Read-only. No inference, no GPU. Ladder (v3_arith_L*) excluded — validated by
validate_arith_ladder.py.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.stdout.reconfigure(encoding="utf-8")

from polagentbench.environments.weather import WeatherEnvironment
from polagentbench.eval.smoke import evaluate
from polagentbench.io import load_task
from polagentbench.protocol import CallTool, FinalAnswer
from polagentbench.types import Trajectory, TrajectoryStep

ADV = Path(__file__).resolve().parent.parent / "tasks" / "adversarial"
LADDER_PREFIX = "v3_arith_L"
_NUM = re.compile(r"^-?\d+([.,]\d+)?$")


def make_step(idx, action, tool_result=None):
    return TrajectoryStep(
        step_idx=idx,
        raw_model_output=json.dumps(action.model_dump(), ensure_ascii=False),
        parsed_action=action,
        tool_result=tool_result,
        latency_ms=0.0,
    )


def chain_of(task):
    efs = task.expected_final_state
    return efs.get("tools_called_in_order_strict") or efs.get("tools_called_in_order") or []


def is_arith(task) -> bool:
    efs = task.expected_final_state
    golden = efs.get("final_answer_contains_any")
    if not golden or not all(_NUM.match(str(g)) for g in golden):
        return False
    ch = chain_of(task)
    has_convert_f = any(
        c.get("tool") == "convert_temperature"
        and (c.get("args") or {}).get("to_unit") == "fahrenheit"
        for c in ch
    )
    has_forecast = any(c.get("tool") == "get_forecast" for c in ch)
    return has_convert_f or has_forecast


def dry_source(task):
    """Replay the chain up to the convert step; return (forecast_temps|None, weather_temp|None)."""
    env = WeatherEnvironment()
    env.reset({})
    fc = None
    wx = None
    for item in chain_of(task):
        tool = item.get("tool")
        args = dict(item.get("args") or {})
        if tool == "convert_temperature":
            break
        res = env.execute_tool(tool, args)
        if not res.get("ok"):
            continue
        if tool == "get_forecast":
            fc = [d["temperature_c"] for d in res["result"]["forecast"]]
        elif tool == "get_weather":
            if wx is None:  # first reading is the conversion source
                wx = res["result"]["temperature_c"]
    return fc, wx


def candidates(fc, wx):
    """Return list of (scheme_name, celsius_value)."""
    out = []
    if fc:
        out.append(("full", sum(fc) / len(fc)))
        if len(fc) >= 4:
            out.append(("day2/day4", (fc[1] + fc[3]) / 2))
    if wx is not None:
        out.append(("single", float(wx)))
    return out


def f_of(c: float) -> float:
    return round(c * 9 / 5 + 32, 2)


def answer_passes_golden(task, f_value: float) -> bool:
    """Minimal trajectory whose ONLY content is the final F answer — tests the golden alone."""
    fa = FinalAnswer(action="final_answer", answer=f"Wynik: {f_value:.2f}°F (czyli {f_value:.1f}).")
    traj = Trajectory(
        task_id=task.id, model_id="o", quant="O", interface_variant=task.language_variant,
        seed=0, steps=[make_step(0, fa)], success=False,
    )
    # check only the final-answer substring, bypassing tool-order:
    from polagentbench.eval.smoke import _check_final_answer_contains_any
    reasons, _ = _check_final_answer_contains_any(
        task.expected_final_state["final_answer_contains_any"], traj
    )
    return not reasons


def pick_scheme(task, fc, wx):
    for name, c in candidates(fc, wx):
        if answer_passes_golden(task, f_of(c)):
            return name, c
    # fallback: nothing matched exactly
    cs = candidates(fc, wx)
    return ("??", cs[0][1]) if cs else ("none", None)


def build_traj(task, source_c: float, mode: str) -> Trajectory:
    """Full real trajectory replaying the strict chain, convert inserted in place."""
    env = WeatherEnvironment()
    env.reset({})
    steps = []
    used = round(source_c, 1) if mode == "rounded" else source_c
    for item in chain_of(task):
        tool = item.get("tool")
        args = dict(item.get("args") or {})
        if tool == "convert_temperature":
            args.setdefault("from_unit", "celsius")
            args.setdefault("to_unit", "fahrenheit")
            args["value"] = round(used, 2)
        res = env.execute_tool(tool, args)
        steps.append(make_step(len(steps), CallTool(action="call_tool", tool=tool, arguments=args), res))

    if mode == "negative":
        answer = f"Temperatura wynosi {source_c:.1f}°C."
    else:
        f_val = f_of(used)
        answer = f"Wynik to {f_val:.2f}°F (czyli {f_val:.1f}°F)."
    steps.append(make_step(len(steps), FinalAnswer(action="final_answer", answer=answer)))
    return Trajectory(
        task_id=task.id, model_id="oracle", quant="ORACLE",
        interface_variant=task.language_variant, seed=0, steps=steps, success=False,
    )


def main() -> int:
    rows = []
    for p in sorted(ADV.glob("*.yaml")):
        task = load_task(p)
        if task.id.startswith(LADDER_PREFIX):
            continue
        if not is_arith(task):
            continue
        fc, wx = dry_source(task)
        scheme, c = pick_scheme(task, fc, wx)
        golden = task.expected_final_state["final_answer_contains_any"]
        f_exact = f_of(c)
        whole = abs(f_exact - round(f_exact)) < 1e-9 and round(f_exact) % 5 == 0

        ok_x = evaluate(task, build_traj(task, c, "exact")).success
        ok_r = evaluate(task, build_traj(task, c, "rounded")).success
        ok_n = evaluate(task, build_traj(task, c, "negative")).success
        mine = ok_x and not ok_r
        rows.append(dict(
            id=task.id, lang=task.language_variant, scheme=scheme,
            c=round(c, 4), f=f_exact, golden=golden, whole=whole,
            x=ok_x, r=ok_r, n=ok_n, mine=mine, clen=len(chain_of(task)),
        ))

    hdr = (f"{'id':<24} {'lang':<6} {'scheme':<10} {'C':<7} {'F':<7} {'golden':<16} "
           f"{'exact':<6} {'round':<6} {'neg':<5} {'MINE':<5} {'÷5':<3}")
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        print(f"{r['id']:<24} {r['lang']:<6} {r['scheme']:<10} {r['c']:<7} {r['f']:<7} "
              f"{str(r['golden']):<16} {('PASS' if r['x'] else 'FAIL'):<6} "
              f"{('PASS' if r['r'] else 'FAIL'):<6} {('FAIL' if not r['n'] else 'PASS!'):<5} "
              f"{('YES' if r['mine'] else '-'):<5} {('!' if r['whole'] else '-'):<3}")

    bad = [r for r in rows if r["mine"] or r["whole"] or r["scheme"] in ("??", "none") or r["x"] is False or r["n"] is True]
    print(f"\nNeeds-fix (mine OR ÷5-whole OR scheme-mismatch OR exact-fail OR neg-pass): {len(bad)}")
    for r in bad:
        why = []
        if r["mine"]: why.append("MINE")
        if r["whole"]: why.append("÷5")
        if r["scheme"] in ("??", "none"): why.append("scheme?")
        if not r["x"]: why.append("exact-FAIL")
        if r["n"]: why.append("neg-PASS")
        print(f"    {r['id']:<24} {','.join(why)}  (golden {r['golden']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
