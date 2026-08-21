# -*- coding: utf-8 -*-
"""
Drabina: kontrola 'to nie sa darmowe punkty' oraz przyczyny L0 = 0.00.

CO LICZY:
Pierwszy blok sprawdza, dlaczego L1 i L2 na 11B Q8 NIE zostaly darowane mimo identycznych
tagow formatu - bo golden jest tam nieobecny (model odpowiada 59 zamiast 46.4, 54.2 zamiast
48.2 i tak dalej). Drugi blok pokazuje, ze L0 = 0.00 we wszystkich osmiu runach ma dwie rozne
przyczyny: 11B lamie zakaz wywolan narzedzi, a 7B i Q2 sa posluszne, ale psuja koperte albo
licza zle.

CZYTA Z:
  jak w ladder_breakdown.py

PRODUKUJE:
  Sesja 2, Analiza 3: kontrola pod TABELA 3 oraz tabela przyczyn L0.

TYLKO ODCZYT - skrypt niczego nie zapisuje ani nie modyfikuje.
Uruchamiac z katalogu glownego repo:
  .venv/Scripts/python.exe analysis/ladder_controls.py
"""
import json,re,sys,glob,yaml,collections
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
GOLD={}
for f in glob.glob("tasks/ladder_ext/v3_ext_*.yaml"):
    d=yaml.safe_load(open(f,encoding="utf-8"))
    GOLD[d["id"]]=[str(x) for x in d["expected_final_state"].get("final_answer_contains_any",[])]
FMT_ONLY={"final_answer_missing","schema_violation","invalid_json","final_answer_shape_violation"}
def json_objects(text):
    out,depth,start,instr,esc=[],0,None,False,False
    for i,ch in enumerate(text):
        if instr:
            if esc: esc=False
            elif ch==chr(92): esc=True
            elif ch=='"': instr=False
            continue
        if ch=='"': instr=True; continue
        if ch=="{":
            if depth==0: start=i
            depth+=1
        elif ch=="}":
            if depth>0:
                depth-=1
                if depth==0 and start is not None:
                    try: out.append(json.loads(text[start:i+1]))
                    except Exception: pass
                    start=None
    return out
def verdicts(run):
    v={}
    for ln in open(f"{run}/run.log",encoding="utf-8"):
        m=re.match(r"^(\S+)\s+([✓✗?])\s+(.*)$",ln.rstrip("\n"))
        if m:
            tail=m.group(3); tg=set()
            if " - " in tail: tg={t.strip() for t in tail.rsplit(" - ",1)[1].split(",")}
            v[m.group(1)]=("PASS" if m.group(2)=="✓" else "FAIL",tg)
    return v
def aval(t):
    for s in reversed(t["steps"]):
        pa=s["parsed_action"] or {}
        if pa.get("action")=="final_answer": return pa.get("answer")
    for s in reversed(t["steps"]):
        for o in json_objects(s["raw_model_output"]):
            if isinstance(o,dict) and o.get("action")=="final_answer" and "answer" in o: return o["answer"]
    return None

run="results/v3_11b_ladder_2026-07-29/q8_no_repair"
v=verdicts(run); trajs={t["task_id"]:t for t in (json.loads(l) for l in open(f"{run}/trajectories.jsonl",encoding="utf-8"))}
print("=== 11B Q8: dlaczego L1/L2 NIE zostaly darowane (kontrola 'to nie sa darmowe punkty') ===")
for R in ["L1","L2"]:
    print(f"\n  --- {R} ---")
    for tid in sorted(k for k in v if k.startswith(f"v3_ext_{R}_")):
        st,tg=v[tid]
        if st=="PASS": print(f"    {tid}  PASS"); continue
        val=aval(trajs[tid]); hit=val is not None and any(g in str(val) for g in GOLD[tid])
        why = "tagi tresciowe" if not (tg and tg<=FMT_ONLY) else ("golden OBECNY" if hit else f"golden BRAK (golden={GOLD[tid][0]}, model={val})")
        print(f"    {tid}  FAIL  tagi={sorted(tg)}  -> {why}")

print()
print("=== L0 = 0.00 we WSZYSTKICH 8 runach — dlaczego (L0 zabrania wywolan narzedzi) ===")
for model,q,run in [("11B","Q8_0","results/v3_11b_ladder_2026-07-29/q8_no_repair"),
                    ("11B","Q3_K_M","results/v3_11b_ladder_2026-07-29/q3_no_repair"),
                    ("7B","Q8_0","results/v3_7b_ladder_2026-07-29/q8_no_repair"),
                    ("11B","Q2_K","results/v3_11b_ladder_2026-07-29/q2_no_repair")]:
    vv=verdicts(run); tt={t["task_id"]:t for t in (json.loads(l) for l in open(f"{run}/trajectories.jsonl",encoding="utf-8"))}
    tags=collections.Counter(); ncalls=[]
    for tid,(st,tg) in vv.items():
        if not tid.startswith("v3_ext_L0_"): continue
        tags.update(tg)
        ncalls.append(sum(1 for s in tt[tid]["steps"] if (s["parsed_action"] or {}).get("action")=="call_tool"))
    print(f"  {model} {q}: tagi L0 = {dict(tags)}   wywolan narzedzi na zadanie = {ncalls}")
