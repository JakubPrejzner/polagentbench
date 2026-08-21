"""KROK 1 — deterministic audit of ALL arith tasks in the hard tier.

For every task in tasks/adversarial with a `final_answer_contains_any` golden,
replay the get_forecast call(s) from its expected tool chain in a live env,
compute both averaging schemes (full forecast mean vs day2/day4 mean), convert
to F, and report which one the golden matches + whether it is a ROUNDING MINE.

Mine criterion (matches the ladder oracle's exact/rounded test): a golden is
mine-FREE iff feeding round(mean, 1) into the C->F conversion still yields a
value whose 2-dp / 1-dp string is accepted by the golden list. If rounding the
mean to 1 dp changes the accepted F string -> MINE.

Also flags whole-/multiple-of-5 °F substring hazards (e.g. 50.0 matched by "50").
Read-only: no edits, no inference, no GPU.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.stdout.reconfigure(encoding="utf-8")

from polagentbench.environments.weather import WeatherEnvironment
from polagentbench.io import load_task

ADV = Path(__file__).resolve().parent.parent / "tasks" / "adversarial"

LADDER_PREFIX = "v3_arith_L"          # already fixed in faa3bfa
ALREADY_FIXED = {"v3_chain_en_013"}   # fixed 2026-06-10


def forecast_temps(city: str, days: int) -> list[float]:
    env = WeatherEnvironment()
    env.reset({})
    res = env.execute_tool("get_forecast", {"city": city, "days": days})
    assert res.get("ok"), f"get_forecast({city},{days}) -> {res}"
    return [d["temperature_c"] for d in res["result"]["forecast"]]


def f_strings(mean_c: float) -> list[str]:
    """All plausible F string forms a model could emit for this Celsius mean."""
    f2 = round(mean_c * 9 / 5 + 32, 2)
    forms = {f"{f2:.2f}", f"{f2:.1f}", f"{round(f2):d}", f"{f2:g}"}
    return sorted(forms)


def golden_accepts(golden: list[str], s: str) -> bool:
    # evaluate() uses normalized substring; here decimal sep is the only wrinkle.
    cands = {s, s.replace(".", ",")}
    return any(any(g in c or c in g for c in cands) for g in golden)


def analyse(task):
    efs = task.expected_final_state
    golden = efs.get("final_answer_contains_any")
    if not golden:
        return None  # not an arith / numeric-answer task

    chain = efs.get("tools_called_in_order_strict") or efs.get("tools_called_in_order") or []
    forecasts = [c for c in chain if c.get("tool") == "get_forecast"]
    if not forecasts:
        return {"id": task.id, "golden": golden, "note": "golden but NO get_forecast (non-mean numeric?)"}

    # Use the LAST forecast in the chain (the one whose mean is reported).
    fc = forecasts[-1]["args"]
    city, days = fc.get("city"), fc.get("days")
    temps = forecast_temps(city, days)

    full_mean = sum(temps) / len(temps)
    d2d4 = (temps[1] + temps[3]) / 2 if len(temps) >= 4 else None

    # which scheme does the golden match (exact mean)?
    scheme = None
    for nm, m in (("full", full_mean), ("day2/day4", d2d4)):
        if m is None:
            continue
        if any(golden_accepts(golden, s) for s in f_strings(m)):
            scheme = nm
            mean_c = m
            break
    if scheme is None:
        # fall back to full mean for reporting
        scheme, mean_c = "??", full_mean

    # MINE test: does rounding the mean to 1 dp still satisfy the golden?
    exact_ok = any(golden_accepts(golden, s) for s in f_strings(mean_c))
    rounded_ok = any(golden_accepts(golden, s) for s in f_strings(round(mean_c, 1)))
    mine = exact_ok and not rounded_ok

    # whole/÷5 °F substring hazard
    f_exact = round(mean_c * 9 / 5 + 32, 2)
    whole_hazard = abs(f_exact - round(f_exact)) < 1e-9 and round(f_exact) % 5 == 0

    return {
        "id": task.id,
        "lang": task.language_variant,
        "city": city,
        "days": days,
        "temps": temps,
        "scheme": scheme,
        "mean_c": round(mean_c, 4),
        "f_exact": f_exact,
        "golden": golden,
        "mine": mine,
        "whole_hazard": whole_hazard,
        "chain_len": len(chain),
        "has_fnc": any(c.get("tool") == "find_nearest_city" for c in chain),
    }


def main() -> int:
    rows = []
    for p in sorted(ADV.glob("*.yaml")):
        task = load_task(p)
        if task.id.startswith(LADDER_PREFIX):
            continue  # ladder already fixed; audited separately
        a = analyse(task)
        if a is None:
            continue
        rows.append(a)

    arith = [r for r in rows if "mean_c" in r]
    other = [r for r in rows if "mean_c" not in r]

    print(f"=== ARITH tasks (golden + get_forecast), excluding ladder ===  ({len(arith)})\n")
    hdr = f"{'id':<26} {'lang':<6} {'city':<10} {'d':<2} {'scheme':<9} {'mean_c':<7} {'F':<7} {'golden':<18} {'MINE':<5} {'÷5':<3} chain"
    print(hdr)
    print("-" * len(hdr))
    for r in sorted(arith, key=lambda r: r["id"]):
        flag_fixed = "  [FIXED]" if r["id"] in ALREADY_FIXED else ""
        print(
            f"{r['id']:<26} {r['lang']:<6} {r['city']:<10} {r['days']:<2} {r['scheme']:<9} "
            f"{r['mean_c']:<7} {r['f_exact']:<7} {str(r['golden']):<18} "
            f"{'YES' if r['mine'] else '-':<5} {'!' if r['whole_hazard'] else '-':<3} "
            f"{r['chain_len']}{'+fnc' if r['has_fnc'] else ''}{flag_fixed}"
        )

    print("\n=== goldens WITHOUT get_forecast (not mean-arith) ===")
    for r in other:
        print(f"  {r['id']:<26} golden={r['golden']}  {r['note']}")

    mines = [r for r in arith if r["mine"] and r["id"] not in ALREADY_FIXED]
    print(f"\n>>> MINES to fix (excl. ladder + already-fixed): {len(mines)}")
    for r in mines:
        print(f"    {r['id']}  ({r['city']} d={r['days']}, golden {r['golden']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
