"""Tests for the weather environment."""

from __future__ import annotations

import pytest

from polagentbench.environments.weather import WeatherEnvironment


@pytest.fixture
def env() -> WeatherEnvironment:
    e = WeatherEnvironment()
    e.reset({})
    return e


def test_available_tool_names(env: WeatherEnvironment):
    names = env.available_tool_names()
    assert set(names) == {
        "get_weather",
        "get_forecast",
        "send_weather_alert",
        "convert_temperature",
        "find_nearest_city",
    }


def test_get_weather_happy_path(env: WeatherEnvironment):
    obs = env.execute_tool("get_weather", {"city": "Kraków"})
    assert obs["ok"] is True
    assert obs["result"]["city"] == "Kraków"
    assert "temperature_c" in obs["result"]
    assert "condition" in obs["result"]
    assert "humidity_pct" in obs["result"]


def test_get_weather_diacritic_stripped_input_resolves(env: WeatherEnvironment):
    obs = env.execute_tool("get_weather", {"city": "Lodz"})
    assert obs["ok"] is True
    assert obs["result"]["city"] == "Łódź"
    last = env.current_state()["lookup_log"][-1]
    assert last["input"] == "Lodz"
    assert last["canonical"] == "Łódź"
    assert last["diacritic_corrupted"] is True


def test_get_weather_canonical_input_no_diacritic_corruption_flag(env: WeatherEnvironment):
    env.execute_tool("get_weather", {"city": "Łódź"})
    last = env.current_state()["lookup_log"][-1]
    assert last["diacritic_corrupted"] is False


def test_get_weather_city_not_found(env: WeatherEnvironment):
    obs = env.execute_tool("get_weather", {"city": "Atlantis"})
    assert obs["ok"] is False
    assert obs["error_code"] == "CITY_NOT_FOUND"
    assert "Atlantis" in obs["error"]


def test_get_forecast_happy_path(env: WeatherEnvironment):
    obs = env.execute_tool("get_forecast", {"city": "Warszawa", "days": 3})
    assert obs["ok"] is True
    assert obs["result"]["days"] == 3
    assert len(obs["result"]["forecast"]) == 3


@pytest.mark.parametrize("days", [0, 8, -1, 100])
def test_get_forecast_invalid_range(env: WeatherEnvironment, days: int):
    obs = env.execute_tool("get_forecast", {"city": "Warszawa", "days": days})
    assert obs["ok"] is False
    assert obs["error_code"] == "INVALID_RANGE"


def test_send_weather_alert_happy_path(env: WeatherEnvironment):
    obs = env.execute_tool(
        "send_weather_alert",
        {"city": "Warszawa", "severity": "high", "message": "Storm incoming."},
    )
    assert obs["ok"] is True
    state = env.current_state()
    assert len(state["alerts_sent"]) == 1
    assert state["alerts_sent"][0]["severity"] == "high"


def test_send_weather_alert_invalid_severity(env: WeatherEnvironment):
    obs = env.execute_tool(
        "send_weather_alert",
        {"city": "Warszawa", "severity": "wysoka", "message": "Burza."},
    )
    assert obs["ok"] is False
    assert obs["error_code"] == "INVALID_ENUM"
    # Bad severity should NOT have been recorded
    assert env.current_state()["alerts_sent"] == []


def test_convert_temperature_celsius_to_fahrenheit(env: WeatherEnvironment):
    obs = env.execute_tool(
        "convert_temperature",
        {"value": 0.0, "from_unit": "celsius", "to_unit": "fahrenheit"},
    )
    assert obs["ok"] is True
    assert obs["result"]["value"] == 32.0


def test_convert_temperature_invalid_unit(env: WeatherEnvironment):
    obs = env.execute_tool(
        "convert_temperature",
        {"value": 10.0, "from_unit": "celsjusz", "to_unit": "fahrenheit"},
    )
    assert obs["ok"] is False
    assert obs["error_code"] == "INVALID_ENUM"


def test_find_nearest_city_happy_path(env: WeatherEnvironment):
    obs = env.execute_tool(
        "find_nearest_city",
        {"reference_city": "Kraków", "max_distance_km": 90},
    )
    assert obs["ok"] is True
    assert "Katowice" in obs["result"]["cities"]
    assert "Tarnów" in obs["result"]["cities"]


def test_find_nearest_city_no_neighbours_returns_empty(env: WeatherEnvironment):
    obs = env.execute_tool(
        "find_nearest_city",
        {"reference_city": "Lisbon", "max_distance_km": 50},
    )
    assert obs["ok"] is True
    assert obs["result"]["cities"] == []


def test_find_nearest_city_unknown_reference(env: WeatherEnvironment):
    obs = env.execute_tool(
        "find_nearest_city",
        {"reference_city": "Atlantis", "max_distance_km": 50},
    )
    assert obs["ok"] is False
    assert obs["error_code"] == "CITY_NOT_FOUND"


def test_unknown_tool(env: WeatherEnvironment):
    obs = env.execute_tool("delete_database", {})
    assert obs["ok"] is False
    assert obs["error_code"] == "UNKNOWN_TOOL"


def test_current_state_reflects_alerts(env: WeatherEnvironment):
    env.execute_tool(
        "send_weather_alert",
        {"city": "Wrocław", "severity": "medium", "message": "Heat wave."},
    )
    env.execute_tool(
        "send_weather_alert",
        {"city": "Warszawa", "severity": "low", "message": "Light rain."},
    )
    state = env.current_state()
    assert len(state["alerts_sent"]) == 2
    assert [a["city"] for a in state["alerts_sent"]] == ["Wrocław", "Warszawa"]


def test_reset_clears_alerts_and_lookup_log():
    env = WeatherEnvironment()
    env.reset({})
    env.execute_tool("get_weather", {"city": "Gdańsk"})
    env.execute_tool(
        "send_weather_alert",
        {"city": "Gdańsk", "severity": "high", "message": "Storm."},
    )
    assert env.current_state()["alerts_sent"]
    assert env.current_state()["lookup_log"]

    env.reset({})
    assert env.current_state()["alerts_sent"] == []
    assert env.current_state()["lookup_log"] == []


def test_reset_seeds_alerts_from_initial_state():
    env = WeatherEnvironment()
    env.reset({"alerts_sent": [{"city": "Kraków", "severity": "low", "message": "x"}]})
    assert len(env.current_state()["alerts_sent"]) == 1


# ---------------------------------------------------------------------------
# Tatry, strict_match and hardcoded_state (prompt 03 additions)
# ---------------------------------------------------------------------------


def test_tatry_is_in_city_db(env: WeatherEnvironment):
    obs = env.execute_tool("get_weather", {"city": "Tatry"})
    assert obs["ok"] is True
    assert obs["result"]["city"] == "Tatry"
    assert obs["result"]["temperature_c"] == -5.0


def test_zory_with_diacritics_resolves(env: WeatherEnvironment):
    obs = env.execute_tool("get_weather", {"city": "Żory"})
    assert obs["ok"] is True
    assert obs["result"]["city"] == "Żory"


def test_strict_match_rejects_diacritic_stripped_input():
    env = WeatherEnvironment()
    env.reset({"__strict_match": True})
    obs = env.execute_tool("get_weather", {"city": "Lodz"})
    assert obs["ok"] is False
    assert obs["error_code"] == "CITY_NOT_FOUND"


def test_strict_match_rejects_inflected_form():
    env = WeatherEnvironment()
    env.reset({"__strict_match": True})
    # "Łodzi" is locative case of "Łódź" — folded form would otherwise resolve.
    obs = env.execute_tool("get_weather", {"city": "Łodzi"})
    assert obs["ok"] is False
    assert obs["error_code"] == "CITY_NOT_FOUND"


def test_strict_match_accepts_canonical_form():
    env = WeatherEnvironment()
    env.reset({"__strict_match": True})
    obs = env.execute_tool("get_weather", {"city": "Łódź"})
    assert obs["ok"] is True
    assert obs["result"]["city"] == "Łódź"


def test_strict_match_default_off_after_plain_reset():
    env = WeatherEnvironment()
    env.reset({"__strict_match": True})
    env.reset({})  # second reset clears strict mode
    obs = env.execute_tool("get_weather", {"city": "Lodz"})
    assert obs["ok"] is True


def test_hardcoded_state_overrides_city_condition():
    env = WeatherEnvironment()
    env.reset({"__overrides": {"cities": {"Warszawa": {"condition": "fog"}}}})
    obs = env.execute_tool("get_weather", {"city": "Warszawa"})
    assert obs["ok"] is True
    assert obs["result"]["condition"] == "fog"
    # Untouched fields stay at module-level defaults.
    assert obs["result"]["temperature_c"] == 9.0


def test_hardcoded_state_does_not_leak_into_other_cities():
    env = WeatherEnvironment()
    env.reset({"__overrides": {"cities": {"Warszawa": {"condition": "fog"}}}})
    env.execute_tool("get_weather", {"city": "Warszawa"})
    obs = env.execute_tool("get_weather", {"city": "Kraków"})
    assert obs["result"]["condition"] == "cloudy"


def test_hardcoded_state_cleared_on_subsequent_reset():
    env = WeatherEnvironment()
    env.reset({"__overrides": {"cities": {"Warszawa": {"condition": "fog"}}}})
    env.reset({})
    obs = env.execute_tool("get_weather", {"city": "Warszawa"})
    assert obs["result"]["condition"] == "cloudy"
