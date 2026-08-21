# -*- coding: utf-8 -*-
"""
Envelope collapse: splaszczone koperty z pozycja w lancuchu oraz punkty (a), (b), (c).

CO LICZY:
Wypisuje kazde wystapienie parse_error[unknown_action] z numerem kroku, nazwa wstawiona
w pole action i pozycja w lancuchu. Liczy (a) ile jest krokow trzecich i ile z nich to
convert_temperature, (b) ile wywolan convert poza trzecim krokiem i ile z nich ma poprawna
koperte, (c) ile krokow trzecich bez convert ma poprawna koperte. Buduje tabele 2x2.
Niepustosc (b) i (c) rozstrzyga, ze zmienne pozycja i narzedzie NIE sa skonfundowane.

CZYTA Z:
  results/v3_pllum_2026-07-29/q8_main_no_repair/trajectories.jsonl,
  results/v3_arith_clean_2026-06-18/q8_no_repair/trajectories.jsonl,
  results/v3_ladder_2026-06-11/q8_no_repair/trajectories.jsonl

PRODUKUJE:
  Sesja 3, Analiza 3: TABELA 3a, TABELA 3b, TABELA 3c.

TYLKO ODCZYT - skrypt niczego nie zapisuje ani nie modyfikuje.
Uruchamiac z katalogu glownego repo:
  .venv/Scripts/python.exe analysis/envelope_positions.py
"""
import json, sys, re, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RUNS = {
 "PLLuM-8B Q8_0 main (18 splaszczen)": "results/v3_pllum_2026-07-29/q8_main_no_repair",
 "Bielik-7B Q8_0 main (arith_clean)":  "results/v3_arith_clean_2026-06-18/q8_no_repair",
 "Bielik-7B Q8_0 main (ladder0611)":   "results/v3_ladder_2026-06-11/q8_no_repair",
}
TRZECI = 2   # step_idx==2 == trzeci krok liczac od 1

def flat_name(raw):
    m=re.search(r'"action"\s*:\s*"([^"]+)"', raw)
    return m.group(1) if m else "(brak pola action)"

for label, RUN in RUNS.items():
    trajs=[json.loads(l) for l in open(f"{RUN}/trajectories.jsonl",encoding="utf-8")]
    steps=[(t["task_id"],s) for t in trajs for s in t["steps"]]
    flat=[(tid,s) for tid,s in steps if s["parse_error"] and s["parse_error"]["category"]=="unknown_action"]
    print("="*118)
    print(f"### {label}     trajektorii={len(trajs)}  krokow={len(steps)}  splaszczonych kopert={len(flat)}")
    print("="*118)
    if label.startswith("PLLuM"):
        print(f"{'#':<3}{'zadanie':<20}{'step_idx':>9}{'krok(1-idx)':>12}{'nazwa w polu action':<26}"
              f"{'poz. w lancuchu':>16}{'udanych call_tool przed':>25}")
        print("-"*118)
        for i,(tid,s) in enumerate(flat,1):
            t=next(x for x in trajs if x["task_id"]==tid)
            before=sum(1 for u in t["steps"] if u["step_idx"]<s["step_idx"]
                       and (u["parsed_action"] or {}).get("action")=="call_tool")
            print(f"{i:<3}{tid:<20}{s['step_idx']:>9}{s['step_idx']+1:>12}{flat_name(s['raw_model_output']):<26}"
                  f"{before+1:>16}{before:>25}")
        print()

    def is_conv(s):
        pa=s["parsed_action"] or {}
        if pa.get("action")=="call_tool": return pa.get("tool")=="convert_temperature"
        if s["parse_error"] and s["parse_error"]["category"]=="unknown_action":
            return flat_name(s["raw_model_output"])=="convert_temperature"
        return False
    def ok_env(s): return s["parse_error"] is None

    third=[s for _,s in steps if s["step_idx"]==TRZECI]
    third_conv=[s for s in third if is_conv(s)]
    third_noconv=[s for s in third if not is_conv(s)]
    conv_all=[s for _,s in steps if is_conv(s)]
    conv_off=[s for s in conv_all if s["step_idx"]!=TRZECI]

    print(f"(a) krokow trzecich (step_idx={TRZECI}) w runie: {len(third)}")
    print(f"    z nich convert_temperature: {len(third_conv)}   ({len(third_conv)/len(third):.1%} o ile >0)" if third else "    brak")
    print(f"(b) wywolan convert_temperature POZA krokiem trzecim: {len(conv_off)}")
    print(f"    z nich z POPRAWNA koperta: {sum(1 for s in conv_off if ok_env(s))}"
          f"   ze splaszczona: {sum(1 for s in conv_off if not ok_env(s))}")
    print(f"(c) krokow trzecich BEZ convert: {len(third_noconv)}")
    print(f"    z nich z POPRAWNA koperta: {sum(1 for s in third_noconv if ok_env(s))}"
          f"   ze splaszczona/bledna: {sum(1 for s in third_noconv if not ok_env(s))}")
    print()
    print("    TABELA 2x2 — poprawnosc koperty wg (pozycja=trzeci krok) x (narzedzie=convert)")
    print(f"      {'':<22}{'koperta OK':>12}{'koperta zla':>13}{'razem':>8}{'udzial zlych':>14}")
    for lbl,grp in (("trzeci krok + conv",third_conv),("trzeci krok, bez conv",third_noconv),
                    ("conv poza 3. krokiem",conv_off),
                    ("reszta krokow",[s for _,s in steps if s["step_idx"]!=TRZECI and not is_conv(s)])):
        o=sum(1 for s in grp if ok_env(s)); b=len(grp)-o
        print(f"      {lbl:<22}{o:>12}{b:>13}{len(grp):>8}{(b/len(grp) if grp else 0):>13.1%}")
    print()
