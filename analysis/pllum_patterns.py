# -*- coding: utf-8 -*-
"""
PLLuM: kwantyfikacja wzorcow protokolu i artefaktow na calym runie.

CO LICZY:
Liczy udzial krokow sparsowanych poprawnie, rozklad poprawnych kopert (call_tool oraz
final_answer), rozklad nazw wstawionych w pole action przy unknown_action, oraz obecnosc
artefaktow: tokeny specjalne, znaczniki [INST], <s>, naglowki rol, symulowany wynik narzedzia,
wiecej niz jeden obiekt JSON w wyjsciu, wyjscia urwane i puste.

CZYTA Z:
  results/v3_pllum_2026-07-29/q8_main_no_repair/trajectories.jsonl

PRODUKUJE:
  Sesja 2, Analiza 1: TABELA 1a (kolumna PLLuM) i sekcja 1b.

TYLKO ODCZYT - skrypt niczego nie zapisuje ani nie modyfikuje.
Uruchamiac z katalogu glownego repo:
  .venv/Scripts/python.exe analysis/pllum_patterns.py
"""
import json, re, sys, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RUN = "results/v3_pllum_2026-07-29/q8_main_no_repair"
trajs = [json.loads(l) for l in open(f"{RUN}/trajectories.jsonl", encoding="utf-8")]

steps = [s for t in trajs for s in t["steps"]]
print(f"trajektorii: {len(trajs)}   krokow lacznie: {len(steps)}")

# 1. ile krokow sparsowalo sie poprawnie i na jaka akcje
ok = collections.Counter(); err = collections.Counter()
for s in steps:
    if s["parse_error"]: err[s["parse_error"]["category"]] += 1
    else: ok[(s["parsed_action"] or {}).get("action", "?")] += 1
tot = len(steps)
print(f"\n--- KROKI: sparsowane poprawnie {sum(ok.values())}/{tot} ({sum(ok.values())/tot:.1%}), bledne {sum(err.values())}/{tot} ({sum(err.values())/tot:.1%})")
print("  poprawne koperty:", dict(ok))
print("  kategorie bledow:", dict(err))

# 2. unknown_action — jaka wartosc pola action model podstawil
flat = collections.Counter()
for s in steps:
    if s["parse_error"] and s["parse_error"]["category"] == "unknown_action":
        m = re.search(r'"action"\s*:\s*"([^"]+)"', s["raw_model_output"])
        flat[m.group(1) if m else "(brak pola action)"] += 1
print(f"\n--- unknown_action ({sum(flat.values())} krokow): jaka nazwe model wstawil w pole \"action\"")
for k, v in flat.most_common(): print(f"      {k:<28} {v}")

# 3. czy prawidlowe koperty call_tool dotycza tych samych narzedzi
called = collections.Counter()
for s in steps:
    pa = s["parsed_action"] or {}
    if pa.get("action") == "call_tool": called[pa.get("tool")] += 1
print(f"\n--- narzedzia wywolane POPRAWNA koperta call_tool ({sum(called.values())}):")
for k, v in called.most_common(): print(f"      {k:<28} {v}")

# 4. artefakty szablonu i przeciek roli
pat = {
    "token specjalny <|...|>":   re.compile(r"<\|[^|]{1,30}\|>"),
    "znacznik [INST]/[/INST]":   re.compile(r"\[/?INST\]"),
    "<s> lub </s>":              re.compile(r"</?s>"),
    "naglowek roli (user:/assistant:/System:)": re.compile(r"(?im)^\s*(user|assistant|system|Uzytkownik|Asystent)\s*:"),
    "SYMULOWANY wynik narzedzia {\"ok\":": re.compile(r'\{\s*"ok"\s*:'),
    ">1 obiekt JSON w jednym wyjsciu": re.compile(r'\}\s*\n\s*\n\s*\{'),
}
hits = {k: 0 for k in pat}
for s in steps:
    for k, rx in pat.items():
        if rx.search(s["raw_model_output"]): hits[k] += 1
print(f"\n--- ARTEFAKTY (liczba krokow z {tot}):")
for k, v in hits.items(): print(f"      {k:<44} {v:>4}  ({v/tot:.1%})")

# 5. czy wyjscia sa urwane
unterminated = sum(1 for s in steps if s["raw_model_output"].count("{") > s["raw_model_output"].count("}"))
empty = sum(1 for s in steps if not s["raw_model_output"].strip())
print(f"      {'urwane (wiecej { niz })':<44} {unterminated:>4}")
print(f"      {'puste wyjscie':<44} {empty:>4}")

# 6. dlugosci
L = sorted(len(s["raw_model_output"]) for s in steps)
print(f"\n--- dlugosc raw_model_output: min={L[0]} mediana={L[len(L)//2]} max={L[-1]}")
