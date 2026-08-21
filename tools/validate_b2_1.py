"""Offline oracle validation for the 10 B2-1 chains (v3_chain_012-016, en_010-014).

Per task: build the ideal trajectory executing REAL env tools, run evaluate(),
require PASS with zero failure_reasons. For arith variants (013, 015, en_013)
additionally assert the YAML golden list equals the env-derived value in the
canonical ["X.Y", "X,Y"] form. No GPU, no inference.
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


class Session:
    """One live env per task; records steps as the ideal model would emit them."""

    def __init__(self) -> None:
        self.env = WeatherEnvironment()
        self.env.reset({})
        self.steps: list[TrajectoryStep] = []

    def call(self, tool: str, **arguments) -> dict:
        action = CallTool(action="call_tool", tool=tool, arguments=arguments)
        result = self.env.execute_tool(tool, arguments)
        assert result.get("ok") is True, f"{tool}({arguments}) failed: {result}"
        self.steps.append(
            TrajectoryStep(
                step_idx=len(self.steps),
                raw_model_output=json.dumps(action.model_dump(), ensure_ascii=False),
                parsed_action=action,
                tool_result=result,
                latency_ms=0.0,
            )
        )
        return result["result"]

    def finish(self, task, answer: str) -> Trajectory:
        fa = FinalAnswer(action="final_answer", answer=answer)
        self.steps.append(
            TrajectoryStep(
                step_idx=len(self.steps),
                raw_model_output=json.dumps(fa.model_dump(), ensure_ascii=False),
                parsed_action=fa,
                latency_ms=0.0,
            )
        )
        return Trajectory(
            task_id=task.id,
            model_id="oracle",
            quant="ORACLE",
            interface_variant=task.language_variant,
            seed=0,
            steps=self.steps,
        )


def fmt(v: float) -> str:
    return f"{v}"


def plan_012(s, task):
    w = s.call("get_weather", city="Wrocław")
    f = s.call("get_forecast", city="Wrocław", days=3)
    temps = [d["temperature_c"] for d in f["forecast"]]
    return s.finish(task, f"Wrocław: teraz {w['temperature_c']}°C, prognoza 3 dni: {temps}°C."), None


def plan_013(s, task):
    w = s.call("get_weather", city="Kraków")
    c = s.call("convert_temperature", value=w["temperature_c"], from_unit="celsius", to_unit="fahrenheit")
    golden = fmt(c["value"])
    return s.finish(task, f"Aktualna temperatura w Krakowie to {golden}°F."), golden


def plan_014(s, task):
    w = s.call("get_weather", city="Gdańsk")
    f = s.call("get_forecast", city="Gdańsk", days=5)
    temps = [d["temperature_c"] for d in f["forecast"]]
    return s.finish(task, f"Gdańsk: teraz {w['temperature_c']}°C, prognoza 5 dni: {temps}°C."), None


def plan_015(s, task):
    w = s.call("get_weather", city="Poznań")
    c = s.call("convert_temperature", value=w["temperature_c"], from_unit="celsius", to_unit="fahrenheit")
    golden = fmt(c["value"])
    return s.finish(task, f"Aktualna temperatura w Poznaniu to {golden}°F."), golden


def plan_016(s, task):
    w = s.call("get_weather", city="Łódź")
    f = s.call("get_forecast", city="Łódź", days=4)
    temps = [d["temperature_c"] for d in f["forecast"]]
    return s.finish(task, f"Łódź: teraz {w['temperature_c']}°C, prognoza 4 dni: {temps}°C."), None


def plan_en_010(s, task):
    s.call("get_weather", city="Madrid")
    f = s.call("get_forecast", city="Madrid", days=6)
    temps = [d["temperature_c"] for d in f["forecast"]]
    c1 = s.call("convert_temperature", value=temps[0], from_unit="celsius", to_unit="fahrenheit")
    c6 = s.call("convert_temperature", value=temps[5], from_unit="celsius", to_unit="fahrenheit")
    r = s.call("get_weather", city="Rome")
    return s.finish(
        task,
        f"Madrid day 1 is {c1['value']}°F and day 6 is {c6['value']}°F; Rome is {r['temperature_c']}°C now.",
    ), None


def plan_en_011(s, task):
    s.call("get_weather", city="Athens")
    f = s.call("get_forecast", city="Athens", days=5)
    temps = [d["temperature_c"] for d in f["forecast"]]
    cmin = s.call("convert_temperature", value=min(temps), from_unit="celsius", to_unit="fahrenheit")
    cmax = s.call("convert_temperature", value=max(temps), from_unit="celsius", to_unit="fahrenheit")
    t = s.call("get_weather", city="Tokyo")
    return s.finish(
        task,
        f"Athens forecast spans {cmin['value']}°F to {cmax['value']}°F; Tokyo is {t['temperature_c']}°C now.",
    ), None


def plan_en_012(s, task):
    s.call("get_weather", city="Berlin")
    fb = s.call("get_forecast", city="Berlin", days=5)
    mean_b = sum(d["temperature_c"] for d in fb["forecast"]) / 5
    cb = s.call("convert_temperature", value=mean_b, from_unit="celsius", to_unit="fahrenheit")
    s.call("get_weather", city="Paris")
    fp = s.call("get_forecast", city="Paris", days=5)
    mean_p = sum(d["temperature_c"] for d in fp["forecast"]) / 5
    cp = s.call("convert_temperature", value=mean_p, from_unit="celsius", to_unit="fahrenheit")
    return s.finish(
        task,
        f"Berlin 5-day average is {cb['value']}°F; Paris 5-day average is {cp['value']}°F.",
    ), None


def plan_en_013(s, task):
    # Rounding-robust redesign (2026-06-10): mean of forecast day 2 and day 4
    # of d=4 is the integer city base (4.0), so any intermediate rounding
    # converts to the same golden 39.2F.
    s.call("get_weather", city="Oslo")
    f = s.call("get_forecast", city="Oslo", days=4)
    temps = [d["temperature_c"] for d in f["forecast"]]
    mean_c = (temps[1] + temps[3]) / 2
    conv = s.call("convert_temperature", value=mean_c, from_unit="celsius", to_unit="fahrenheit")
    golden = fmt(conv["value"])
    s.call("get_weather", city="Stockholm")
    s.call(
        "send_weather_alert",
        city="Stockholm",
        severity="high",
        message=f"Cold spell: Oslo day-2/day-4 average {mean_c}C is below 5C.",
    )
    return s.finish(task, f"The average of Oslo day 2 and day 4 is {golden}°F; alert sent."), golden


def plan_en_014(s, task):
    s.call("get_weather", city="New York")
    f = s.call("get_forecast", city="New York", days=6)
    temps = [d["temperature_c"] for d in f["forecast"]]
    c1 = s.call("convert_temperature", value=temps[0], from_unit="celsius", to_unit="fahrenheit")
    c6 = s.call("convert_temperature", value=temps[5], from_unit="celsius", to_unit="fahrenheit")
    lon = s.call("get_weather", city="London")
    return s.finish(
        task,
        f"New York day 1 is {c1['value']}°F and day 6 is {c6['value']}°F; London is {lon['temperature_c']}°C now.",
    ), None


PLANS = {
    "v3_chain_012": plan_012,
    "v3_chain_013": plan_013,
    "v3_chain_014": plan_014,
    "v3_chain_015": plan_015,
    "v3_chain_016": plan_016,
    "v3_chain_en_010": plan_en_010,
    "v3_chain_en_011": plan_en_011,
    "v3_chain_en_012": plan_en_012,
    "v3_chain_en_013": plan_en_013,
    "v3_chain_en_014": plan_en_014,
}


def main() -> int:
    all_ok = True
    print(f"{'task_id':<18} | {'n_tools':<7} | {'golden':<7} | verdict")
    print("-" * 60)
    for task_id, plan in PLANS.items():
        task = load_task(ADV / f"{task_id}.yaml")
        n_tools = len(task.expected_final_state["tools_called_in_order_strict"])
        session = Session()
        traj, golden = plan(session, task)

        if golden is not None:
            yaml_goldens = task.expected_final_state.get("final_answer_contains_any")
            expected = [golden, golden.replace(".", ",")]
            if yaml_goldens != expected:
                all_ok = False
                print(f"{task_id:<18} | {n_tools:<7} | {golden:<7} | GOLDEN MISMATCH: yaml={yaml_goldens} env={expected}")
                continue

        res = evaluate(task, traj)
        ok = res.success and not res.failure_reasons
        all_ok &= ok
        verdict = "PASS" if ok else f"{res.status} reasons={res.failure_reasons}"
        print(f"{task_id:<18} | {n_tools:<7} | {golden or '—':<7} | {verdict}")
    print()
    print("B2-1:", "10/10 PASS" if all_ok else "FAILURES PRESENT — see above")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
