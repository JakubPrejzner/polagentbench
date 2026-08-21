# -*- coding: utf-8 -*-
"""
Drabina: pass rate per szczebel oraz rozbicie L3N na SKROT i PRAWDZIWY.

CO LICZY:
Dla osmiu runow drabiny (2 modele x 4 kwanty, repair off) liczy pass rate osobno dla L0, L1,
L2, L3T i L3N. Dla L3N dzieli porazki na SKROT (golden obecny przy jednej konwersji zamiast
dwoch) i PRAWDZIWY, i podaje rate scisla oraz tolerancyjna. Wynik: SKROT nie wystepuje ANI
RAZU w 80 zadaniach L3N, wiec rata tolerancyjna rowna sie scislej. Kolumna RAZEM sluzy jako
kontrola poprawnosci odczytu - musi zgadzac sie z num_passed w summary.json.

CZYTA Z:
  results/v3_11b_ladder_2026-07-29/*/{run.log,trajectories.jsonl},
  results/v3_7b_ladder_2026-07-29/*/{run.log,trajectories.jsonl}, tasks/ladder_ext/*.yaml

PRODUKUJE:
  Sesja 2, Analiza 3: TABELA 1 i TABELA 2.

TYLKO ODCZYT - skrypt niczego nie zapisuje ani nie modyfikuje.
Uruchamiac z katalogu glownego repo:
  .venv/Scripts/python.exe analysis/ladder_breakdown.py
"""
import json, re, sys, glob, yaml, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RUNS = [("Bielik-11B","Q8_0","results/v3_11b_ladder_2026-07-29/q8_no_repair"),
        ("Bielik-11B","Q4_K_M","results/v3_11b_ladder_2026-07-29/q4_no_repair"),
        ("Bielik-11B","Q3_K_M","results/v3_11b_ladder_2026-07-29/q3_no_repair"),
        ("Bielik-11B","Q2_K","results/v3_11b_ladder_2026-07-29/q2_no_repair"),
        ("Bielik-7B", "Q8_0","results/v3_7b_ladder_2026-07-29/q8_no_repair"),
        ("Bielik-7B", "Q4_K_M","results/v3_7b_ladder_2026-07-29/q4_no_repair"),
        ("Bielik-7B", "Q3_K_M","results/v3_7b_ladder_2026-07-29/q3_no_repair"),
        ("Bielik-7B", "Q2_K","results/v3_7b_ladder_2026-07-29/q2_no_repair")]

GOLD = {}
for f in glob.glob("tasks/ladder_ext/v3_ext_*.yaml"):
    d = yaml.safe_load(open(f, encoding="utf-8"))
    GOLD[d["id"]] = [str(x) for x in d["expected_final_state"].get("final_answer_contains_any", [])]

RUNGS = ["L0","L1","L2","L3T","L3N"]
def rung(tid):
    m = re.match(r"v3_ext_(L3N|L3T|L0|L1|L2)_", tid)
    return m.group(1) if m else None

def verdicts(run):
    v = {}
    for ln in open(f"{run}/run.log", encoding="utf-8"):
        m = re.match(r"^(\S+)\s+([✓✗?])\s+(.*)$", ln.rstrip("\n"))
        if m:
            tail = m.group(3); tg = set()
            if " - " in tail: tg = {t.strip() for t in tail.rsplit(" - ",1)[1].split(",")}
            v[m.group(1)] = ("PASS" if m.group(2)=="✓" else "FAIL", tg)
    return v

def json_objects(text):
    """Wyluskaj obiekty JSON skanerem nawiasow — bez regexow z ucieczkami."""
    out, depth, start, instr, esc = [], 0, None, False, False
    for i, ch in enumerate(text):
        if instr:
            if esc: esc = False
            elif ch == chr(92): esc = True
            elif ch == '"': instr = False
            continue
        if ch == '"': instr = True; continue
        if ch == "{":
            if depth == 0: start = i
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    try: out.append(json.loads(text[start:i+1]))
                    except Exception: pass
                    start = None
    return out

def answer_text(t):
    """Tekst final_answer: najpierw sparsowany, potem surowy (moze byc liczba)."""
    for s in reversed(t["steps"]):
        pa = s["parsed_action"] or {}
        if pa.get("action") == "final_answer":
            return str(pa.get("answer", "")), "parsed"
    for s in reversed(t["steps"]):
        for o in json_objects(s["raw_model_output"]):
            if isinstance(o, dict) and o.get("action") == "final_answer" and "answer" in o:
                return str(o["answer"]), "raw"
    return "", "brak"

def n_conv(t):
    return sum(1 for s in t["steps"]
               if (s["parsed_action"] or {}).get("action") == "call_tool"
               and (s["parsed_action"] or {}).get("tool") == "convert_temperature")

DATA = collections.OrderedDict()
for model, quant, run in RUNS:
    v = verdicts(run)
    trajs = {t["task_id"]: t for t in (json.loads(l) for l in open(f"{run}/trajectories.jsonl", encoding="utf-8"))}
    per = {r: [0,0] for r in RUNGS}
    l3n = dict(skrot=[], prawdziwy=[], passed=[])
    for tid, (st, tg) in v.items():
        r = rung(tid)
        if r is None: continue
        per[r][1] += 1
        if st == "PASS": per[r][0] += 1
        if r == "L3N":
            if st == "PASS": l3n["passed"].append(tid); continue
            t = trajs[tid]
            ans, src = answer_text(t)
            hit = any(g in ans for g in GOLD[tid])
            c = n_conv(t)
            if hit and c == 1: l3n["skrot"].append((tid, c, src, ans[:70]))
            else: l3n["prawdziwy"].append((tid, c, hit, src, ans[:70], sorted(tg)))
    DATA[(model, quant)] = (per, l3n)

print("TABELA 1 — pass rate per szczebel (repair OFF, T=0, seed=42)")
print(f"{'model':<12}{'kwant':<9}" + "".join(f"{r+' (n='+str(DATA[list(DATA)[0]][0][r][1])+')':>14}" for r in RUNGS) + f"{'RAZEM':>15}")
print("-"*(21+14*5+15))
for (model,quant),(per,_) in DATA.items():
    tp = sum(p for p,_ in per.values()); tt = sum(t for _,t in per.values())
    cells = "".join(f"{f'{p}/{t}  {p/t:.2f}':>14}" for p,t in (per[r] for r in RUNGS))
    print(f"{model:<12}{quant:<9}{cells}{f'{tp}/{tt}  {tp/tt:.3f}':>15}")

print()
print("TABELA 2 — L3N: rozbicie porazek, dwie pass raty (n=10)")
print(f"{'model':<12}{'kwant':<9}{'PASS':>6}{'SKROT':>7}{'PRAWDZ':>8}{'scisla':>14}{'tolerancyjna':>16}")
print("-"*72)
for (model,quant),(_,l3n) in DATA.items():
    p,s,r = len(l3n["passed"]), len(l3n["skrot"]), len(l3n["prawdziwy"])
    print(f"{model:<12}{quant:<9}{p:>6}{s:>7}{r:>8}{f'{p}/10 = {p/10:.2f}':>14}{f'{p+s}/10 = {(p+s)/10:.2f}':>16}")

print()
print("KONTROLA — pelne wyliczenie L3N, zeby nic sie nie chowalo")
for (model,quant),(_,l3n) in DATA.items():
    print(f"\n### {model} {quant}   PASS={len(l3n['passed'])} SKROT={len(l3n['skrot'])} PRAWDZIWY={len(l3n['prawdziwy'])}  (suma musi byc 10)")
    for tid,c,src,ans in l3n["skrot"]:
        print(f"   SKROT      {tid}  konwersji={c}  golden OBECNY ({src})  answer={ans!r}")
    agg = collections.Counter((c,hit) for _,c,hit,_,_,_ in l3n["prawdziwy"])
    for (c,hit),n in sorted(agg.items()):
        print(f"   PRAWDZIWY  konwersji={c}  golden={'TAK' if hit else 'nie'}  -> {n} zadan")
