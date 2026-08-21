"""Offline oracle validation for the v3 arith isolation ladder (L0-L3).

Rounding-robust redesign (2026-06-18, day2/day4 pattern as in en_013 ef122d4):
the arith is now the mean of forecast day 2 and day 4 of a 4-DAY forecast
(day2 = base-0.5, day4 = base+0.5 -> mean = city base EXACTLY), so any 1-dp
rounding of the mean yields the same F. This replaces the old full-5-day mean,
whose means ended in .76/.24 and required full precision (the rounding mine).

Instances (forecast city / base C / L3 chain):
    a: Łódź    8.0  via Warszawa->Łódź   r=130  -> 46.4 F
    b: Warszawa 9.0 via Łódź->Warszawa   r=130  -> 48.2 F   (moved off Berlin
       10.0 because 10.0 -> 50.0 F is a whole number, a substring-match hazard)
    c: Kraków  7.5  via Katowice->Kraków r=80   -> 45.5 F   (half-integer base;
       day2/day4 mean is exactly 7.5, still 1-dp-rounding-robust)

For each of the 12 tasks it builds THREE trajectories and runs evaluate():
1. EXACT    — ideal path, mean fed at full precision -> must PASS.
2. ROUNDED  — same path but the mean is round(mean,1) before C->F (the mine
              simulation) -> must PASS (proves the mine is gone).
3. NEGATIVE — ideal tool calls but the final answer reports the unconverted
              Celsius mean (forgot C->F) -> must FAIL.

Plus: YAML goldens must equal the env-derived golden; per instance (a/b/c) all
four levels share one golden (isolation); the available_tools block is identical
across all 12 AND identical to v3_chain_001's. No GPU, no inference — oracle only.
"""

from __future__ import annotations

import json
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

# instance -> (L0-L2 forecast city / expected L3 target, L3 chain source, radius km)
INSTANCES = {
    "a": ("Łódź", "Warszawa", 130),
    "b": ("Warszawa", "Łódź", 130),
    "c": ("Kraków", "Katowice", 80),
}
N_TOOLS = {0: 0, 1: 1, 2: 2, 3: 4}
FORECAST_DAYS = 4


def run_tool(env: WeatherEnvironment, tool: str, args: dict) -> dict:
    res = env.execute_tool(tool, args)
    assert res.get("ok") is True, f"{tool}({args}) failed: {res}"
    return res


def make_step(idx: int, action, tool_result=None) -> TrajectoryStep:
    return TrajectoryStep(
        step_idx=idx,
        raw_model_output=json.dumps(action.model_dump(), ensure_ascii=False),
        parsed_action=action,
        tool_result=tool_result,
        latency_ms=0.0,
    )


def call(tool: str, **arguments) -> CallTool:
    return CallTool(action="call_tool", tool=tool, arguments=arguments)


def build_trajectory(task, level: int, inst: str, mode: str) -> tuple[Trajectory, str]:
    """Build a solution path in {exact, rounded, negative} mode, executing every
    tool in a live env. Returns (trajectory, env_derived_golden_F)."""
    assert mode in ("exact", "rounded", "negative")
    env = WeatherEnvironment()
    env.reset({})
    city, source, radius = INSTANCES[inst]
    steps: list[TrajectoryStep] = []

    if level == 3:
        a = call("get_weather", city=source)
        steps.append(make_step(len(steps), a, run_tool(env, a.tool, a.arguments)))
        a = call("find_nearest_city", reference_city=source, max_distance_km=radius)
        r = run_tool(env, a.tool, a.arguments)
        steps.append(make_step(len(steps), a, r))
        city = r["result"]["cities"][0]  # FIRST returned, per the order trap

    if level >= 1:
        a = call("get_forecast", city=city, days=FORECAST_DAYS)
        r = run_tool(env, a.tool, a.arguments)
        steps.append(make_step(len(steps), a, r))
        temps = [d["temperature_c"] for d in r["result"]["forecast"]]
    else:
        # L0: the prompt hands over the same numbers the forecast would return
        r = run_tool(env, "get_forecast", {"city": city, "days": FORECAST_DAYS})
        temps = [d["temperature_c"] for d in r["result"]["forecast"]]
        env.reset({})  # discard: L0's ideal trajectory must contain no calls

    # day 2 (index 1) and day 4 (index 3): offsets -0.5/+0.5 cancel -> mean = base
    mean_c = (temps[1] + temps[3]) / 2
    mean_used = round(mean_c, 1) if mode == "rounded" else mean_c

    # env-derived golden is always from the EXACT mean (independent of mode)
    golden = f"{round(mean_c * 9 / 5 + 32, 2):.1f}"

    if level >= 2:
        a = call(
            "convert_temperature",
            value=round(mean_used, 2),
            from_unit="celsius",
            to_unit="fahrenheit",
        )
        r = run_tool(env, a.tool, a.arguments)
        steps.append(make_step(len(steps), a, r))
        answer_f = f"{r['result']['value']:.1f}"
    else:
        answer_f = f"{mean_used * 9 / 5 + 32:.1f}"

    if mode == "negative":
        # Forgot the C->F conversion: report the Celsius mean instead.
        answer_text = f"Średnia temperatura wynosi {mean_c:.1f}°C."
    else:
        answer_text = f"Średnia temperatura wynosi {answer_f}°F."

    fa = FinalAnswer(action="final_answer", answer=answer_text)
    steps.append(make_step(len(steps), fa))

    traj = Trajectory(
        task_id=task.id,
        model_id="oracle",
        quant="ORACLE",
        interface_variant=task.language_variant,
        seed=0,
        steps=steps,
        success=False,
    )
    return traj, golden


def verdict(task, traj) -> tuple[bool, str]:
    res = evaluate(task, traj)
    if res.success:
        return True, "PASS"
    return False, f"FAIL {res.failure_tags}"


def main() -> int:
    ref_tools = load_task(ADV / "v3_chain_001.yaml").available_tools
    rows = []
    golden_by_cell: dict[tuple[int, str], str] = {}
    all_ok = True

    for level in (0, 1, 2, 3):
        for inst in ("a", "b", "c"):
            task = load_task(ADV / f"v3_arith_L{level}_{inst}.yaml")
            assert task.available_tools == ref_tools, f"{task.id}: tool block drift"
            assert task.language_variant == "PL_EN", task.id

            traj_x, golden = build_trajectory(task, level, inst, "exact")
            traj_r, _ = build_trajectory(task, level, inst, "rounded")
            traj_n, _ = build_trajectory(task, level, inst, "negative")

            yaml_goldens = task.expected_final_state["final_answer_contains_any"]
            assert yaml_goldens == [golden, golden.replace(".", ",")], (
                f"{task.id}: YAML goldens {yaml_goldens} != env-derived {golden!r}"
            )

            ok_x, v_x = verdict(task, traj_x)   # must PASS
            ok_r, v_r = verdict(task, traj_r)   # must PASS (mine gone)
            ok_n, v_n = verdict(task, traj_n)   # must FAIL

            cell_ok = ok_x and ok_r and (not ok_n)
            all_ok = all_ok and cell_ok
            golden_by_cell[(level, inst)] = golden
            rows.append((task.id, golden, v_x, v_r, v_n, cell_ok))

    print(
        f"{'task':<16} | {'golden_°F':<9} | {'dokładna':<8} | {'zaokrągl.':<9} | "
        f"{'negatywna':<14} | ok"
    )
    print("-" * 78)
    for tid, gold, v_x, v_r, v_n, cell_ok in rows:
        mark = "✓" if cell_ok else "✗ ROZJAZD"
        print(f"{tid:<16} | {gold:<9} | {v_x:<8} | {v_r:<9} | {v_n:<14} | {mark}")

    print("\nIzolacja (golden L0=L1=L2=L3 per instancja):")
    for inst in ("a", "b", "c"):
        vals = {golden_by_cell[(lv, inst)] for lv in (0, 1, 2, 3)}
        marker = "IDENTYCZNE" if len(vals) == 1 else "ROZJAZD!"
        print(f"  instancja {inst}: {sorted(vals)} -> {marker}")
        if len(vals) != 1:
            all_ok = False

    distinct = {golden_by_cell[(0, i)] for i in ("a", "b", "c")}
    print(f"\nGoldeny międzyinstancyjne: {sorted(distinct)} "
          f"({'wszystkie odrębne' if len(distinct) == 3 else 'KOLIZJA!'})")
    if len(distinct) != 3:
        all_ok = False

    n_ok = sum(1 for r in rows if r[5])
    print(f"\n{n_ok}/12 czyste (dokładna+zaokrąglona PASS, negatywna FAIL, izolacja OK)")
    return 0 if all_ok and n_ok == 12 else 1


if __name__ == "__main__":
    raise SystemExit(main())
