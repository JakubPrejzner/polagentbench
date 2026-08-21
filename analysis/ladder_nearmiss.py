# -*- coding: utf-8 -*-
"""
Drabina: co zabija L3N przy poprawnym lancuchu i poprawnej liczbie.

CO LICZY:
Dla porazek L3N z dokladnie dwiema konwersjami wypisuje lancuch, zrodlo i typ pola answer
oraz tagi oracle. Pokazuje, dlaczego kategoria SKROT jest pusta: model robi wymagany lancuch
i podaje golden, a odpada na TYPIE pola answer - float w 11B, dict w 7B - przy schemacie
wymagajacym stringa.

CZYTA Z:
  results/v3_11b_ladder_2026-07-29/{q8,q4}_no_repair/,
  results/v3_7b_ladder_2026-07-29/{q8,q4}_no_repair/, tasks/ladder_ext/v3_ext_L3N_*.yaml

PRODUKUJE:
  Sesja 2, Analiza 3: blok 'Dlaczego SKROT jest pusty'.

TYLKO ODCZYT - skrypt niczego nie zapisuje ani nie modyfikuje.
Uruchamiac z katalogu glownego repo:
  .venv/Scripts/python.exe analysis/ladder_nearmiss.py
"""
import json, re, sys, glob, yaml, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GOLD={}
for f in glob.glob("tasks/ladder_ext/v3_ext_L3N_*.yaml"):
    d=yaml.safe_load(open(f,encoding="utf-8"))
    GOLD[d["id"]]=[str(x) for x in d["expected_final_state"]["final_answer_contains_any"]]
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
RUNS=[("Bielik-11B","Q8_0","results/v3_11b_ladder_2026-07-29/q8_no_repair"),
      ("Bielik-11B","Q4_K_M","results/v3_11b_ladder_2026-07-29/q4_no_repair"),
      ("Bielik-7B","Q8_0","results/v3_7b_ladder_2026-07-29/q8_no_repair"),
      ("Bielik-7B","Q4_K_M","results/v3_7b_ladder_2026-07-29/q4_no_repair")]
for model,quant,run in RUNS:
    v=verdicts(run)
    trajs={t["task_id"]:t for t in (json.loads(l) for l in open(f"{run}/trajectories.jsonl",encoding="utf-8"))}
    print(f"\n{'='*100}\n### {model} {quant} — L3N, porazki z DWIEMA konwersjami\n{'='*100}")
    for tid in sorted(k for k in v if k.startswith("v3_ext_L3N_")):
        st,tg=v[tid]
        if st=="PASS": continue
        t=trajs[tid]
        chain=[(s["parsed_action"] or {}).get("tool") for s in t["steps"] if (s["parsed_action"] or {}).get("action")=="call_tool"]
        nconv=sum(1 for c in chain if c=="convert_temperature")
        if nconv!=2: continue
        # final answer: parsed?
        parsed=None
        for s in reversed(t["steps"]):
            pa=s["parsed_action"] or {}
            if pa.get("action")=="final_answer": parsed=pa.get("answer"); break
        rawans=None; rawtype=None
        if parsed is None:
            for s in reversed(t["steps"]):
                for o in json_objects(s["raw_model_output"]):
                    if isinstance(o,dict) and o.get("action")=="final_answer" and "answer" in o:
                        rawans=o["answer"]; rawtype=type(o["answer"]).__name__; break
                if rawans is not None: break
        val = parsed if parsed is not None else rawans
        hit = any(g in str(val) for g in GOLD[tid]) if val is not None else False
        src = "SPARSOWANY(str)" if parsed is not None else (f"TYLKO SUROWY({rawtype})" if rawans is not None else "BRAK")
        print(f"  {tid}  lancuch={'>'.join(x[:4] for x in chain)}")
        print(f"      final_answer: {src}  golden={'TAK' if hit else 'NIE'}  wartosc={str(val)[:70]!r}")
        print(f"      tagi oracle: {sorted(tg)}")
