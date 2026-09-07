# -*- coding: utf-8 -*-
"""
Drabina: rata tolerancyjna wg faktycznej przyczyny odrzucenia, czyli typowania pola answer.

CO LICZY:
Skoro SKROT jest pusty, liczy trzecia rate: daruje wylacznie porazki, w ktorych oracle nie
zglosil zadnego zarzutu do lancucha (same tagi formatu) I wartosc final_answer zawiera golden,
ale nie jest stringiem. L3N na 11B Q8 idzie 0.20 na 0.90, na 7B Q8 z 0.00 na 0.70.
Zadania L1 i L2 celowo NIE sa darowane, bo tam golden jest nieobecny - patrz ladder_controls.py.

CZYTA Z:
  jak w ladder_breakdown.py

PRODUKUJE:
  Sesja 2, Analiza 3: TABELA 3.

TYLKO ODCZYT - skrypt niczego nie zapisuje ani nie modyfikuje.
Uruchamiac z katalogu glownego repo:
  .venv/Scripts/python.exe analysis/ladder_typing_tolerant.py
"""
import json, re, sys, glob, yaml, collections
from release_paths import resolve_run_paths
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
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
def verdicts(run_log):
    v={}
    for ln in open(run_log,encoding="utf-8"):
        m=re.match(r"^(\S+)\s+([✓✗?])\s+(.*)$",ln.rstrip("\n"))
        if m:
            tail=m.group(3); tg=set()
            if " - " in tail: tg={t.strip() for t in tail.rsplit(" - ",1)[1].split(",")}
            v[m.group(1)]=("PASS" if m.group(2)=="✓" else "FAIL",tg)
    return v
def answer_val(t):
    for s in reversed(t["steps"]):
        pa=s["parsed_action"] or {}
        if pa.get("action")=="final_answer": return pa.get("answer")
    for s in reversed(t["steps"]):
        for o in json_objects(s["raw_model_output"]):
            if isinstance(o,dict) and o.get("action")=="final_answer" and "answer" in o: return o["answer"]
    return None
RUNS=[("Bielik-11B","Q8_0","results/v3_11b_ladder_2026-07-29/q8_no_repair"),
      ("Bielik-11B","Q4_K_M","results/v3_11b_ladder_2026-07-29/q4_no_repair"),
      ("Bielik-11B","Q3_K_M","results/v3_11b_ladder_2026-07-29/q3_no_repair"),
      ("Bielik-11B","Q2_K","results/v3_11b_ladder_2026-07-29/q2_no_repair"),
      ("Bielik-7B","Q8_0","results/v3_7b_ladder_2026-07-29/q8_no_repair"),
      ("Bielik-7B","Q4_K_M","results/v3_7b_ladder_2026-07-29/q4_no_repair"),
      ("Bielik-7B","Q3_K_M","results/v3_7b_ladder_2026-07-29/q3_no_repair"),
      ("Bielik-7B","Q2_K","results/v3_7b_ladder_2026-07-29/q2_no_repair")]
RUNGS=["L0","L1","L2","L3T","L3N"]
def rung(t):
    m=re.match(r"v3_ext_(L3N|L3T|L0|L1|L2)_",t); return m.group(1) if m else None

print("TABELA 3 — rata TOLERANCYJNA NA TYPOWANIE: darowane sa wylacznie porazki,")
print("           w ktorych oracle NIE zglosil zadnego zarzutu do lancucha (tylko tagi formatu)")
print("           I wartosc final_answer zawiera golden, ale nie jest stringiem.")
print()
hdr=f"{'model':<12}{'kwant':<9}"+"".join(f"{r:>18}" for r in RUNGS)+f"{'RAZEM':>19}"
print(hdr); print("-"*len(hdr))
TOT={}
for model,quant,run in RUNS:
    paths=resolve_run_paths(run)
    v=verdicts(paths.run_log)
    trajs={t["task_id"]:t for t in (json.loads(l) for l in open(paths.trajectories,encoding="utf-8"))}
    per={r:[0,0,0] for r in RUNGS}   # [strict_pass, forgiven, total]
    for tid,(st,tg) in v.items():
        r=rung(tid)
        if r is None: continue
        per[r][2]+=1
        if st=="PASS": per[r][0]+=1; continue
        if tg and tg<=FMT_ONLY:
            val=answer_val(trajs[tid])
            if val is not None and not isinstance(val,str) and any(g in str(val) for g in GOLD[tid]):
                per[r][1]+=1
    cells="".join(f"{f'{p}+{fg}={p+fg}/{t} ({(p+fg)/t:.2f})':>18}" for p,fg,t in (per[r] for r in RUNGS))
    P=sum(x[0] for x in per.values()); F=sum(x[1] for x in per.values()); T=sum(x[2] for x in per.values())
    print(f"{model:<12}{quant:<9}{cells}{f'{P}+{F}={P+F}/{T} ({(P+F)/T:.3f})':>19}")
    TOT[(model,quant)]=(P,F,T)
print()
print("Legenda komorki:  scisle_PASS + darowane_na_typowaniu = razem/n (rata)")
print()
print("Podsumowanie L3N — trzy raty obok siebie:")
print(f"{'model':<12}{'kwant':<9}{'scisla':>12}{'tolerancyjna SKROT':>22}{'tolerancyjna TYPOWANIE':>26}")
print("-"*81)
for model,quant,run in RUNS:
    paths=resolve_run_paths(run)
    v=verdicts(paths.run_log)
    trajs={t["task_id"]:t for t in (json.loads(l) for l in open(paths.trajectories,encoding="utf-8"))}
    p=fg=0
    for tid,(st,tg) in v.items():
        if rung(tid)!="L3N": continue
        if st=="PASS": p+=1; continue
        if tg and tg<=FMT_ONLY:
            val=answer_val(trajs[tid])
            if val is not None and not isinstance(val,str) and any(g in str(val) for g in GOLD[tid]): fg+=1
    print(f"{model:<12}{quant:<9}{f'{p}/10 = {p/10:.2f}':>12}{f'{p}/10 = {p/10:.2f}':>22}{f'{p+fg}/10 = {(p+fg)/10:.2f}':>26}")

# --- BLOK DODANY: liczby, ktore cytuje przypis pod tabela sensitivity w paperze ---
# Nic powyzej nie jest zmieniane; ponizsze wiersze tylko DRUKUJA to, co i tak wynika
# z tej samej reguly kredytowania, zebrane po wszystkich osmiu runach.
print()
print("Pula po osmiu runach (suma kolumny RAZEM powyzej):")
_P=sum(p for p,f,t in TOT.values()); _F=sum(f for p,f,t in TOT.values()); _T=sum(t for p,f,t in TOT.values())
print(f"  scisle        {_P}/{_T} = {_P/_T:.3f}")
print(f"  tolerancyjnie {_P+_F}/{_T} = {(_P+_F)/_T:.3f}")
print(f"  delta         {_F}/{_T} = {_F/_T:.3f}")
print()
print("Spis porazek CZYSTO FORMATOWYCH (tagi niepuste i zawarte w FMT_ONLY) po osmiu runach")
print("oraz powod, dla ktorego korekta ich NIE kredytuje:")
_fmt=_cred=_no_val=_is_str=_no_gold=0
for model,quant,run in RUNS:
    paths=resolve_run_paths(run)
    v=verdicts(paths.run_log)
    trajs={t["task_id"]:t for t in (json.loads(l) for l in open(paths.trajectories,encoding="utf-8"))}
    for tid,(st,tg) in v.items():
        if rung(tid) is None or st=="PASS": continue
        if not (tg and tg<=FMT_ONLY): continue
        _fmt+=1
        val=answer_val(trajs[tid])
        if val is None: _no_val+=1
        elif isinstance(val,str): _is_str+=1
        elif any(g in str(val) for g in GOLD[tid]): _cred+=1
        else: _no_gold+=1
print(f"  porazki czysto formatowe                              {_fmt}")
print(f"    kredytowane przez korekte (kryteria i+ii+iii)       {_cred}")
print(f"    NIE kredytowane                                     {_fmt-_cred}")
print(f"      (iii) wartosc odzyskana, nie-str, brak goldena    {_no_gold}")
print(f"      (ii)  wartosci answer w ogole nie dalo sie odzyskac {_no_val}")
print(f"      (iii) odzyskana wartosc JEST typu str             {_is_str}")
print(f"    kontrola sumy: {_cred}+{_no_gold}+{_no_val}+{_is_str} = {_cred+_no_gold+_no_val+_is_str} (musi byc {_fmt})")
