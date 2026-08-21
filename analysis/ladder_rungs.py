# -*- coding: utf-8 -*-
"""
Drabina: definicje szczebli L0, L1, L2, L3N, L3T prosto z YAML.

CO LICZY:
Dla pierwszej instancji kazdego szczebla wypisuje uzyty check, oczekiwany lancuch narzedzi,
liczbe wymaganych konwersji, max_steps i golden. Ustala fakty, na ktorych stoi cala analiza
drabiny: L0 ZABRANIA wywolan narzedzi (no_tool_calls), L3N wymaga dwoch osobnych konwersji,
L3T ma pulapke kolejnosci przy jednej konwersji.

CZYTA Z:
  tasks/ladder_ext/*.yaml

PRODUKUJE:
  Sesja 2, Analiza 3: naglowek sekcji z opisem szczebli.

TYLKO ODCZYT - skrypt niczego nie zapisuje ani nie modyfikuje.
Uruchamiac z katalogu glownego repo:
  .venv/Scripts/python.exe analysis/ladder_rungs.py
"""
import sys, glob, yaml, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
for rung in ["L0","L1","L2","L3N","L3T"]:
    fs = sorted(glob.glob(f"tasks/ladder_ext/v3_ext_{rung}_*.yaml"))
    d = yaml.safe_load(open(fs[0], encoding="utf-8"))
    sp = d["expected_final_state"]
    chain = None
    for k in ("tools_called_in_order_strict","tools_called_in_order","ordered_tools","tools_called_in_order_loose"):
        if k in sp: chain = (k, sp[k]); break
    seq = " > ".join(c["tool"] for c in chain[1]) if chain else "(brak lancucha)"
    nconv = sum(1 for c in chain[1] if c["tool"]=="convert_temperature") if chain else 0
    print(f"{rung:<5} instancji={len(fs):<3} check={chain[0] if chain else '-':<28} max_steps={d['max_steps']}")
    print(f"      lancuch: {seq}")
    print(f"      konwersji wymaganych: {nconv}   checki: {sorted(sp.keys())}")
    print(f"      golden: {sp.get('final_answer_contains_any')}")
    print()
