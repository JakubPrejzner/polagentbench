# -*- coding: utf-8 -*-
"""Kanoniczny klasyfikator trybow porazki uzyty w paperze.

CO LICZY:
Przypisuje kazdej porazce dokladnie jedna etykiete z czterech:
PROTOCOL_SHAPE / GENUINE_ARITH / TOOL_FIXATION / ROUNDING_MINE (piata, "other",
jest kategoria resztkowa i na zbiorze arytmetycznym pozostaje pusta).
Regula jest JEDNOETYKIETOWA z TWARDYM PRIORYTETEM: pierwsza pasujaca galaz wygrywa.
Kolejnosc galezi jest czescia definicji, nie szczegolem implementacji -- odwrocenie
priorytetu przeetykietowuje 72% porazek PLLuM (patrz Appendix "Taxonomy" w paperze).

PROWENANCJA:
Kod przeniesiony bez zmiany semantyki z results/v3_arith_clean_2026-06-18/analyze_clean.py
(md5 ebffc05a62a84559a2e6f6cfa94fef9c; bajt w bajt identyczny z
results/v3_arith_clean_2026-06-18/analysis/analyze.py). To ta wersja odtwarza liczby
raportowane w paperze. Dwie inne kopie na dysku NIE sa kanoniczne i roznia sie definicjami:
  results/v3_11b_2026-06-18/analysis/analyze.py   (md5 7e2359..., stale z sufiksem _7B)
  results/v3_ladder_2026-06-11/analysis/analyze.py (md5 134b42..., katalog na commicie
                                                    niezgodnym z HEAD, nie jest zrodlem)
Katalog results/ jest gitignorowany, wiec przed tym przeniesieniem klasyfikator obiecany
w abstrakcie nie istnial w opublikowanej czesci repo.

ZBIOR ZADAN ARYTMETYCZNYCH (n=25) wyznacza is_arith_task(), regula skopiowana z tego
samego pliku: 12 zadan drabiny pilotowej v3_arith_L{0,1,2,3}_{a,b,c} plus 13 lancuchow
arytmetycznych (id konczace sie na "_arith" oraz trzy wyjatki wymienione z nazwy).

TYLKO ODCZYT - modul nie zapisuje niczego.
Uzycie:
  import sys; sys.path.insert(0, "analysis")
  from failure_classifier import classify_failure, is_arith_task
"""
from __future__ import annotations

import re

__all__ = [
    "PROTOCOL_TAGS",
    "FIXATION_TAGS",
    "ROUNDING_WINDOW",
    "classify_failure",
    "is_arith_task",
    "active_branches",
]

# --- zbiory tagow, dokladnie jak w analyze_clean.py -------------------------
PROTOCOL_TAGS = {
    "invalid_json",
    "no_json_found",
    "schema_violation",
    "unknown_action",
    "final_answer_shape_violation",
}
FIXATION_TAGS = {
    "final_answer_missing",
    "wrong_tool_order",
    "unexpected_tool_call",
    "min_tool_calls",
    "timeout",
}

# Okno tolerancji dla artefaktu zaokragleniowego. 0.06 dobrane tak, zeby zlapac
# roznice jednego miejsca dziesietnego po konwersji C->F, a nie zlapac realnych pomylek.
ROUNDING_WINDOW = 0.06

_ARITH_LADDER = re.compile(r"^v3_arith_L\d_[abc]$")
_ARITH_CHAIN_EXCEPTIONS = {"v3_chain_013", "v3_chain_015", "v3_chain_en_013"}


def is_arith_task(task_id: str) -> bool:
    """Czy zadanie nalezy do 25-elementowego zbioru ocenianego arytmetycznie."""
    if _ARITH_LADDER.match(task_id):
        return True
    return task_id.endswith("_arith") or task_id in _ARITH_CHAIN_EXCEPTIONS


def classify_failure(tags, answer_text, golden_floats):
    """Jedna etykieta dla jednej porazki. Priorytet regul jest wiazacy.

    Args:
        tags: zbior tagow oracle dla tej porazki.
        answer_text: tekst final_answer modelu (moze byc pusty albo None).
        golden_floats: lista wartosci goldenu jako float.

    Returns:
        "ROUNDING_MINE" | "GENUINE_ARITH" | "PROTOCOL_SHAPE" | "TOOL_FIXATION" | "other"
    """
    tags = set(tags or ())

    # Galaz 1: model podal odpowiedz, ale zla. Rozstrzygamy, czy to artefakt
    # zaokraglenia (wartosc trafia w okno wokol goldenu), czy prawdziwy blad rachunku.
    if "wrong_final_answer" in tags:
        ans = (answer_text or "").replace(",", ".")
        nums = [float(x) for x in re.findall(r"-?\d+\.?\d*", ans)]
        for g in golden_floats or ():
            if any(abs(n - g) <= ROUNDING_WINDOW for n in nums):
                return "ROUNDING_MINE"
        return "GENUINE_ARITH"

    # Galaz 2: koperta akcji nie przeszla parsera albo walidacji schematu.
    if tags & PROTOCOL_TAGS:
        return "PROTOCOL_SHAPE"

    # Galaz 3: lancuch narzedzi poszedl nie tak, choc format byl poprawny.
    if tags & FIXATION_TAGS:
        return "TOOL_FIXATION"

    return "other"


def active_branches(tags):
    """Ile galezi decyzyjnych jest aktywnych dla tego zbioru tagow.

    Miara determinacji etykiety: 1 oznacza, ze priorytet regul nie ma znaczenia,
    a 2 lub 3, ze etykieta jest wynikiem arbitralnej kolejnosci.
    Zwraca krotke (wrong_final_answer, protocol, fixation) wartosci bool.
    """
    tags = set(tags or ())
    return (
        "wrong_final_answer" in tags,
        bool(tags & PROTOCOL_TAGS),
        bool(tags & FIXATION_TAGS),
    )
