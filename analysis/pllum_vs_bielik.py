# -*- coding: utf-8 -*-
"""
PLLuM wobec Bielik-11B Q8: metryki protokolu i rozklad tagow.

CO LICZY:
Zestawia oba runy na tych samych 67 zadaniach przy tym samym seedzie i temperaturze.
Werdykty PLLuM bierze z run.log, werdykty Bielika z per_task_matrix.csv, bo katalog czerwcowy
nie ma run.log. Dzieli tagi na FORMAT i TRESC i pokazuje, ze rozklad jest odwrocony: Bielik
przegrywa glownie na formacie (43 wobec 15), PLLuM glownie na tresci (74 wobec 29).

CZYTA Z:
  results/v3_pllum_2026-07-29/q8_main_no_repair/, results/v3_11b_2026-06-18/q8_no_repair/,
  results/v3_11b_2026-06-18/analysis/per_task_matrix.csv

PRODUKUJE:
  Sesja 2, Analiza 1: TABELA 1a i TABELA 1c.

TYLKO ODCZYT - skrypt niczego nie zapisuje ani nie modyfikuje.
Uruchamiac z katalogu glownego repo:
  .venv/Scripts/python.exe analysis/pllum_vs_bielik.py
"""
import json, re, sys, csv, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

P_RUN = "results/v3_pllum_2026-07-29/q8_main_no_repair"
B_RUN = "results/v3_11b_2026-06-18/q8_no_repair"
B_CSV = "results/v3_11b_2026-06-18/analysis/per_task_matrix.csv"

FORMAT_TAGS  = {"unknown_action", "no_json_found", "invalid_json", "schema_violation",
                "final_answer_shape_violation", "final_answer_missing"}
CONTENT_TAGS = {"wrong_final_answer", "wrong_tool_order", "expected_tool_not_called",
                "unexpected_tool_call", "unauthorized_side_effect", "hallucinated_tool_result",
                "tool_call_failed", "timeout"}

def pllum_verdicts():
    v = {}
    for ln in open(f"{P_RUN}/run.log", encoding="utf-8"):
        m = re.match(r"^(\S+)\s+([✓✗?])\s+(.*)$", ln.rstrip("\n"))
        if m:
            tail = m.group(3); tags = []
            if " - " in tail: tags = [t.strip() for t in tail.rsplit(" - ", 1)[1].split(",")]
            v[m.group(1)] = ("PASS" if m.group(2) == "✓" else "FAIL", set(tags))
    return v

def bielik_verdicts():
    v = {}
    for r in csv.DictReader(open(B_CSV, encoding="utf-8")):
        tags = {t for t in (r["tags_q8_no_repair"] or "").split(";") if t}
        v[r["task_id"]] = (r["q8_no_repair"], tags)
    return v

def metrics(run, verds, label):
    sm = json.load(open(f"{run}/summary.json", encoding="utf-8"))
    trajs = [json.loads(l) for l in open(f"{run}/trajectories.jsonl", encoding="utf-8")]
    steps = [st for t in trajs for st in t["steps"]]
    n = len(steps)
    ok  = sum(1 for st in steps if not st["parse_error"])
    ct  = sum(1 for st in steps if (st["parsed_action"] or {}).get("action") == "call_tool")
    fa  = sum(1 for st in steps if (st["parsed_action"] or {}).get("action") == "final_answer")
    tmpl= sum(1 for st in steps if re.search(r"<\|[^|]{1,30}\|>|\[/?INST\]|</?s>", st["raw_model_output"]))
    role= sum(1 for st in steps if re.search(r'\{\s*"ok"\s*:', st["raw_model_output"]))
    multi=sum(1 for st in steps if re.search(r'\}\s*\n\s*\n\s*\{', st["raw_model_output"]))
    fails = [ (t, tg) for t,(s,tg) in verds.items() if s == "FAIL" ]
    only_fmt = sum(1 for _, tg in fails if not (tg & CONTENT_TAGS))
    with_cont= sum(1 for _, tg in fails if tg & CONTENT_TAGS)
    return dict(label=label, sm=sm, n=n, ok=ok, ct=ct, fa=fa, tmpl=tmpl, role=role, multi=multi,
                nfail=len(fails), only_fmt=only_fmt, with_cont=with_cont,
                seeds=sorted({t["seed"] for t in trajs}), temps=sorted({t["temperature"] for t in trajs}),
                steps_per_traj=n/len(trajs))

P = metrics(P_RUN, pllum_verdicts(), "PLLuM-8B Q8_0")
B = metrics(B_RUN, bielik_verdicts(), "Bielik-11B Q8_0")

w = 22
print(f"{'metryka':<50}{P['label']:>{w}}{B['label']:>{w}}")
print("-" * (50 + 2*w))
def L(lbl, fp, fb=None):
    fb = fb or fp
    print(f"{lbl:<50}{str(fp(P)):>{w}}{str(fb(B)):>{w}}")
L("num_passed / num_total", lambda r: f"{r['sm']['num_passed']}/{r['sm']['num_total']}")
L("success_rate",           lambda r: r['sm']['success_rate'])
L("seed / temperature",     lambda r: f"{r['seeds']} / {r['temps']}")
print()
L("krokow lacznie",                       lambda r: r['n'])
L("krokow / trajektorie",                 lambda r: f"{r['steps_per_traj']:.2f}")
L("krokow sparsowanych POPRAWNIE",        lambda r: f"{r['ok']} ({r['ok']/r['n']:.1%})")
L("  poprawnych kopert call_tool",        lambda r: r['ct'])
L("  poprawnych kopert final_answer",     lambda r: r['fa'])
print()
L("artefakty szablonu (<|..|> / [INST] / <s>)",   lambda r: r['tmpl'])
L("symulowany wynik narzedzia {\"ok\": ...}",     lambda r: f"{r['role']} ({r['role']/r['n']:.1%})")
L(">1 obiekt JSON w jednym wyjsciu",              lambda r: f"{r['multi']} ({r['multi']/r['n']:.1%})")
print()
L("porazek lacznie",                              lambda r: r['nfail'])
L("  porazki CZYSTO formatowe (bez tagu tresci)", lambda r: r['only_fmt'])
L("  porazki z tagiem TRESCIOWYM",                lambda r: r['with_cont'])
L("  sufit przy zerowaniu bledow formatu",        lambda r: f"{r['sm']['num_total']-r['with_cont']}/{r['sm']['num_total']} = {(r['sm']['num_total']-r['with_cont'])/r['sm']['num_total']:.3f}")

print("\n\n=== ROZKLAD failure_tag_counts (summary.json, zliczenia wystapien) ===")
pa, bb = P['sm']['failure_tag_counts'], B['sm']['failure_tag_counts']
allt = sorted(set(pa) | set(bb), key=lambda t: -(pa.get(t,0)+bb.get(t,0)))
print(f"{'tag':<32}{'rodzaj':<9}{'PLLuM-8B Q8':>14}{'Bielik-11B Q8':>16}")
print("-" * 71)
for t in allt:
    kind = "FORMAT" if t in FORMAT_TAGS else ("TRESC" if t in CONTENT_TAGS else "?")
    print(f"{t:<32}{kind:<9}{pa.get(t,0):>14}{bb.get(t,0):>16}")
print("-" * 71)
print(f"{'SUMA FORMAT':<41}{sum(v for k,v in pa.items() if k in FORMAT_TAGS):>14}{sum(v for k,v in bb.items() if k in FORMAT_TAGS):>16}")
print(f"{'SUMA TRESC':<41}{sum(v for k,v in pa.items() if k in CONTENT_TAGS):>14}{sum(v for k,v in bb.items() if k in CONTENT_TAGS):>16}")
