"""Weather environment.

Stateless except for an in-memory log of alerts the agent has dispatched
during the current task run. Provides five tools designed to surface the
failure modes the benchmark cares about:

* ``get_weather`` / ``get_forecast`` — straightforward lookup; exercise
  city-name normalisation and date-range validation.
* ``send_weather_alert`` — has an enum-typed ``severity`` argument; the
  primary surface for ``language_leakage`` (model emits Polish "wysoka" in
  place of English "high").
* ``convert_temperature`` — also enum-typed (``celsius``/``fahrenheit``);
  catches unit-confusion failures.
* ``find_nearest_city`` — distractor tool; useful for ``WRONG_TOOL``
  detection in later evaluators.

City names are normalised (NFKD strip + Polish ``ł``/``Ł`` mapping +
lowercase) so models that drop diacritics still get a result. Each lookup
records the input form alongside the canonical form in ``lookup_log`` so
downstream analysis can quantify diacritic-corruption rates without
penalising the smoke-stage agent.
"""

from __future__ import annotations

import unicodedata
from typing import Any

from .base import Environment

__all__ = ["WeatherEnvironment"]


# ---------------------------------------------------------------------------
# City database
# ---------------------------------------------------------------------------
#
# Real meteorology this isn't — values are illustrative and chosen so that
# tasks have a stable, deterministic ground truth. Polish cities first, then
# major European + a handful of others.

_CITIES: dict[str, dict[str, Any]] = {
    # --- Poland (32) ---
    "Warszawa": {"temperature_c": 9.0, "condition": "cloudy", "humidity_pct": 70},
    "Kraków": {"temperature_c": 7.5, "condition": "cloudy", "humidity_pct": 72},
    "Łódź": {"temperature_c": 8.0, "condition": "rain", "humidity_pct": 80},
    "Wrocław": {"temperature_c": 10.0, "condition": "clear", "humidity_pct": 60},
    "Poznań": {"temperature_c": 8.5, "condition": "rain", "humidity_pct": 78},
    "Gdańsk": {"temperature_c": 7.0, "condition": "windy", "humidity_pct": 82},
    "Szczecin": {"temperature_c": 9.0, "condition": "cloudy", "humidity_pct": 75},
    "Bydgoszcz": {"temperature_c": 8.0, "condition": "cloudy", "humidity_pct": 73},
    "Lublin": {"temperature_c": 7.0, "condition": "clear", "humidity_pct": 65},
    "Białystok": {"temperature_c": 5.5, "condition": "rain", "humidity_pct": 81},
    "Katowice": {"temperature_c": 8.0, "condition": "cloudy", "humidity_pct": 70},
    "Gdynia": {"temperature_c": 7.5, "condition": "windy", "humidity_pct": 80},
    "Częstochowa": {"temperature_c": 7.5, "condition": "cloudy", "humidity_pct": 71},
    "Radom": {"temperature_c": 8.0, "condition": "cloudy", "humidity_pct": 70},
    "Sosnowiec": {"temperature_c": 8.0, "condition": "cloudy", "humidity_pct": 70},
    "Toruń": {"temperature_c": 8.5, "condition": "rain", "humidity_pct": 76},
    "Kielce": {"temperature_c": 7.0, "condition": "cloudy", "humidity_pct": 69},
    "Rzeszów": {"temperature_c": 7.0, "condition": "clear", "humidity_pct": 64},
    "Gliwice": {"temperature_c": 8.0, "condition": "cloudy", "humidity_pct": 70},
    "Olsztyn": {"temperature_c": 6.5, "condition": "rain", "humidity_pct": 79},
    "Bielsko-Biała": {"temperature_c": 6.0, "condition": "snow", "humidity_pct": 85},
    "Opole": {"temperature_c": 9.0, "condition": "clear", "humidity_pct": 62},
    "Tarnów": {"temperature_c": 8.0, "condition": "cloudy", "humidity_pct": 68},
    "Płock": {"temperature_c": 8.5, "condition": "cloudy", "humidity_pct": 72},
    "Elbląg": {"temperature_c": 7.0, "condition": "windy", "humidity_pct": 80},
    "Włocławek": {"temperature_c": 8.5, "condition": "rain", "humidity_pct": 77},
    "Zakopane": {"temperature_c": 2.0, "condition": "snow", "humidity_pct": 88},
    "Świnoujście": {"temperature_c": 8.0, "condition": "windy", "humidity_pct": 84},
    "Sopot": {"temperature_c": 7.5, "condition": "windy", "humidity_pct": 81},
    "Zielona Góra": {"temperature_c": 9.5, "condition": "clear", "humidity_pct": 63},
    "Żory": {"temperature_c": 8.0, "condition": "cloudy", "humidity_pct": 70},
    "Tatry": {"temperature_c": -5.0, "condition": "snow", "humidity_pct": 88},
    # --- International (20) ---
    "London": {"temperature_c": 11.0, "condition": "rain", "humidity_pct": 78},
    "Paris": {"temperature_c": 12.0, "condition": "cloudy", "humidity_pct": 70},
    "Berlin": {"temperature_c": 10.0, "condition": "cloudy", "humidity_pct": 72},
    "Madrid": {"temperature_c": 17.0, "condition": "clear", "humidity_pct": 45},
    "Rome": {"temperature_c": 18.0, "condition": "clear", "humidity_pct": 55},
    "Vienna": {"temperature_c": 11.0, "condition": "cloudy", "humidity_pct": 65},
    "Prague": {"temperature_c": 10.0, "condition": "cloudy", "humidity_pct": 67},
    "Budapest": {"temperature_c": 12.0, "condition": "clear", "humidity_pct": 60},
    "Amsterdam": {"temperature_c": 11.0, "condition": "rain", "humidity_pct": 80},
    "Brussels": {"temperature_c": 11.0, "condition": "cloudy", "humidity_pct": 75},
    "Stockholm": {"temperature_c": 5.0, "condition": "cloudy", "humidity_pct": 73},
    "Oslo": {"temperature_c": 4.0, "condition": "snow", "humidity_pct": 80},
    "Copenhagen": {"temperature_c": 8.0, "condition": "cloudy", "humidity_pct": 78},
    "Helsinki": {"temperature_c": 3.0, "condition": "snow", "humidity_pct": 82},
    "Lisbon": {"temperature_c": 16.0, "condition": "clear", "humidity_pct": 60},
    "Athens": {"temperature_c": 19.0, "condition": "clear", "humidity_pct": 50},
    "Dublin": {"temperature_c": 10.0, "condition": "rain", "humidity_pct": 82},
    "Reykjavik": {"temperature_c": 4.0, "condition": "windy", "humidity_pct": 80},
    "New York": {"temperature_c": 14.0, "condition": "cloudy", "humidity_pct": 65},
    "Tokyo": {"temperature_c": 17.0, "condition": "clear", "humidity_pct": 60},
}


# Hand-curated neighbour graph for `find_nearest_city`. Distances are
# approximate straight-line km; only canonical city names appear as keys.
_NEIGHBOURS: dict[str, list[tuple[str, int]]] = {
    "Warszawa": [("Łódź", 130), ("Płock", 110), ("Radom", 100), ("Lublin", 165)],
    "Kraków": [("Katowice", 80), ("Tarnów", 85), ("Zakopane", 105), ("Opole", 175)],
    "Wrocław": [("Opole", 100), ("Poznań", 165), ("Katowice", 195)],
    "Gdańsk": [("Sopot", 15), ("Gdynia", 25), ("Elbląg", 60), ("Olsztyn", 170)],
    "Łódź": [("Warszawa", 130), ("Częstochowa", 120), ("Płock", 100)],
    "Poznań": [("Wrocław", 165), ("Bydgoszcz", 130), ("Zielona Góra", 145)],
    "Katowice": [("Kraków", 80), ("Gliwice", 25), ("Sosnowiec", 15), ("Bielsko-Biała", 50)],
    "Gdynia": [("Sopot", 5), ("Gdańsk", 25)],
    "Sopot": [("Gdynia", 5), ("Gdańsk", 15)],
}


# Polish ``ł``/``Ł`` aren't decomposable via NFKD, so map them explicitly.
_ASCII_FOLD = {"ł": "l", "Ł": "L"}


def _normalize_key(name: str) -> str:
    """Fold a city name into a diacritic-insensitive lookup key.

    NFKD-decomposes the input, drops combining marks, replaces Polish
    ``ł``/``Ł`` (which NFKD does not handle), and lowercases. Used purely
    for lookup; the canonical form returned by the env still preserves
    diacritics.
    """
    nfkd = unicodedata.normalize("NFKD", name)
    no_diacritic = "".join(c for c in nfkd if not unicodedata.combining(c))
    folded = "".join(_ASCII_FOLD.get(c, c) for c in no_diacritic)
    return folded.lower().strip()


_LOOKUP_INDEX: dict[str, str] = {_normalize_key(c): c for c in _CITIES}

_VALID_SEVERITY = {"low", "medium", "high"}
_VALID_TEMP_UNIT = {"celsius", "fahrenheit"}


_RESERVED_STRICT_MATCH_KEY = "__strict_match"
_RESERVED_OVERRIDES_KEY = "__overrides"


class WeatherEnvironment(Environment):
    """Concrete weather environment used by the smoke-test suite.

    Honours two reserved keys on the ``initial_state`` dict passed to
    :meth:`reset`, populated by the runner from the corresponding fields on
    :class:`~polagentbench.types.Task`:

    * ``__strict_match`` — bool. When True, :meth:`_resolve_city` requires
      exact equality with a canonical city name; diacritic and inflection
      folding are disabled. Used by tasks that intentionally measure
      ``DIACRITIC_CORRUPTION`` / ``INFLECTION_MISMATCH``.
    * ``__overrides`` — namespaced dict, e.g. ``{"cities": {"Poznań":
      {"condition": "rain"}}}``. Per-key overrides are layered on top of the
      built-in city record at lookup time so adversarial tasks can pin a
      condition without mutating the module-level city DB.
    """

    def __init__(self) -> None:
        self._alerts_sent: list[dict[str, Any]] = []
        self._lookup_log: list[dict[str, Any]] = []
        self._strict_match: bool = False
        self._city_overrides: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Environment ABC
    # ------------------------------------------------------------------

    def reset(self, initial_state: dict[str, Any]) -> None:
        """Discard alerts and lookup log; absorb optional reserved keys."""
        self._alerts_sent = list(initial_state.get("alerts_sent", []))
        self._lookup_log = []
        self._strict_match = bool(initial_state.get(_RESERVED_STRICT_MATCH_KEY, False))
        overrides = initial_state.get(_RESERVED_OVERRIDES_KEY) or {}
        cities_override = overrides.get("cities") if isinstance(overrides, dict) else None
        self._city_overrides = (
            {k: dict(v) for k, v in cities_override.items() if isinstance(v, dict)}
            if isinstance(cities_override, dict)
            else {}
        )

    def current_state(self) -> dict[str, Any]:
        return {
            "alerts_sent": list(self._alerts_sent),
            "lookup_log": list(self._lookup_log),
        }

    def available_tool_names(self) -> list[str]:
        return [
            "get_weather",
            "get_forecast",
            "send_weather_alert",
            "convert_temperature",
            "find_nearest_city",
        ]

    def execute_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        handler = _HANDLERS.get(name)
        if handler is None:
            return {
                "ok": False,
                "error": f"Unknown tool: {name!r}. Available: {self.available_tool_names()}.",
                "error_code": "UNKNOWN_TOOL",
            }
        return handler(self, arguments)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _resolve_city(self, raw: Any) -> tuple[str | None, dict[str, Any] | None]:
        """Resolve a raw city argument to its canonical entry.

        Returns ``(canonical_name, record)`` on success and ``(None, None)``
        otherwise. Always logs the attempt to ``lookup_log`` so analysis can
        attribute diacritic-corruption rates per task.

        In strict mode, only an exact match against a canonical city name is
        accepted; diacritic and inflection folding are bypassed, surfacing
        the underlying corruption as a CITY_NOT_FOUND error.
        """
        if not isinstance(raw, str) or not raw.strip():
            self._lookup_log.append(
                {"input": raw, "canonical": None, "diacritic_corrupted": False, "found": False}
            )
            return None, None

        if self._strict_match:
            canonical = raw if raw in _CITIES else None
            if canonical is None:
                self._lookup_log.append(
                    {
                        "input": raw,
                        "canonical": None,
                        "diacritic_corrupted": False,
                        "found": False,
                    }
                )
                return None, None
            self._lookup_log.append(
                {
                    "input": raw,
                    "canonical": canonical,
                    "diacritic_corrupted": False,
                    "found": True,
                }
            )
            return canonical, self._record_for(canonical)

        key = _normalize_key(raw)
        canonical = _LOOKUP_INDEX.get(key)
        if canonical is None:
            self._lookup_log.append(
                {
                    "input": raw,
                    "canonical": None,
                    "diacritic_corrupted": False,
                    "found": False,
                }
            )
            return None, None
        corrupted = raw != canonical and _normalize_key(canonical) == key
        self._lookup_log.append(
            {
                "input": raw,
                "canonical": canonical,
                "diacritic_corrupted": corrupted,
                "found": True,
            }
        )
        return canonical, self._record_for(canonical)

    def _record_for(self, canonical: str) -> dict[str, Any]:
        """Return the city record with any per-task field overrides layered on top."""
        base = _CITIES[canonical]
        override = self._city_overrides.get(canonical)
        if not override:
            return dict(base)
        return {**base, **override}


# ---------------------------------------------------------------------------
# Tool handlers — module-level closures keyed in ``_HANDLERS``
# ---------------------------------------------------------------------------


def _city_not_found(name: str) -> dict[str, Any]:
    return {
        "ok": False,
        "error": f"City {name!r} not found in database.",
        "error_code": "CITY_NOT_FOUND",
    }


def _get_weather(env: WeatherEnvironment, args: dict[str, Any]) -> dict[str, Any]:
    canonical, record = env._resolve_city(args.get("city"))
    if canonical is None:
        return _city_not_found(args.get("city", ""))
    return {"ok": True, "result": {"city": canonical, **record}}


def _get_forecast(env: WeatherEnvironment, args: dict[str, Any]) -> dict[str, Any]:
    canonical, record = env._resolve_city(args.get("city"))
    if canonical is None:
        return _city_not_found(args.get("city", ""))
    days = args.get("days")
    if not isinstance(days, int) or isinstance(days, bool) or not 1 <= days <= 7:
        return {
            "ok": False,
            "error": "days must be an integer between 1 and 7.",
            "error_code": "INVALID_RANGE",
        }
    base_temp = record["temperature_c"]
    forecast = [
        {
            "day": i + 1,
            "temperature_c": round(base_temp + (i - days / 2) * 0.5, 1),
            "condition": record["condition"],
        }
        for i in range(days)
    ]
    return {"ok": True, "result": {"city": canonical, "days": days, "forecast": forecast}}


def _send_weather_alert(env: WeatherEnvironment, args: dict[str, Any]) -> dict[str, Any]:
    canonical, _ = env._resolve_city(args.get("city"))
    if canonical is None:
        return _city_not_found(args.get("city", ""))
    severity = args.get("severity")
    if severity not in _VALID_SEVERITY:
        return {
            "ok": False,
            "error": f"severity must be one of: {sorted(_VALID_SEVERITY)}.",
            "error_code": "INVALID_ENUM",
        }
    message = args.get("message")
    if not isinstance(message, str) or not message.strip():
        return {
            "ok": False,
            "error": "message must be a non-empty string.",
            "error_code": "INVALID_ARGUMENT",
        }
    alert = {"city": canonical, "severity": severity, "message": message}
    env._alerts_sent.append(alert)
    return {"ok": True, "result": {"alert": alert, "alert_id": len(env._alerts_sent)}}


def _convert_temperature(env: WeatherEnvironment, args: dict[str, Any]) -> dict[str, Any]:
    value = args.get("value")
    from_unit = args.get("from_unit")
    to_unit = args.get("to_unit")
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return {
            "ok": False,
            "error": "value must be a number.",
            "error_code": "INVALID_ARGUMENT",
        }
    if from_unit not in _VALID_TEMP_UNIT or to_unit not in _VALID_TEMP_UNIT:
        return {
            "ok": False,
            "error": f"unit must be one of: {sorted(_VALID_TEMP_UNIT)}.",
            "error_code": "INVALID_ENUM",
        }
    if from_unit == to_unit:
        result = float(value)
    elif from_unit == "celsius":
        result = float(value) * 9 / 5 + 32
    else:
        result = (float(value) - 32) * 5 / 9
    return {
        "ok": True,
        "result": {
            "value": round(result, 2),
            "from_unit": from_unit,
            "to_unit": to_unit,
        },
    }


def _find_nearest_city(env: WeatherEnvironment, args: dict[str, Any]) -> dict[str, Any]:
    canonical, _ = env._resolve_city(args.get("reference_city"))
    if canonical is None:
        return _city_not_found(args.get("reference_city", ""))
    max_distance = args.get("max_distance_km")
    if not isinstance(max_distance, int) or isinstance(max_distance, bool) or max_distance <= 0:
        return {
            "ok": False,
            "error": "max_distance_km must be a positive integer.",
            "error_code": "INVALID_ARGUMENT",
        }
    candidates = _NEIGHBOURS.get(canonical, [])
    matches = [city for city, distance in candidates if distance <= max_distance]
    return {
        "ok": True,
        "result": {
            "reference_city": canonical,
            "max_distance_km": max_distance,
            "cities": matches,
        },
    }


_HANDLERS = {
    "get_weather": _get_weather,
    "get_forecast": _get_forecast,
    "send_weather_alert": _send_weather_alert,
    "convert_temperature": _convert_temperature,
    "find_nearest_city": _find_nearest_city,
}
