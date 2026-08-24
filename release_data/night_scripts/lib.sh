#!/usr/bin/env bash
# PolAgentBench night session 2026-07-29 — shared helpers.
# Lives in night/ (NOT src/, NOT tasks/) — rule 5 compliant.
set -uo pipefail

REPO_ROOT=/workspace/polagentbench
LOG="$REPO_ROOT/results/NIGHT_LOG.txt"
FLAGS="$REPO_ROOT/night/flags"
mkdir -p "$FLAGS" "$REPO_ROOT/results"

NVLIB=$("$REPO_ROOT/.venv/bin/python" -c "import nvidia;print(list(nvidia.__path__)[0])")
export LD_LIBRARY_PATH="$NVLIB/cublas/lib:$NVLIB/cuda_runtime/lib:$NVLIB/cuda_nvrtc/lib:${LD_LIBRARY_PATH:-}"
export HF_HUB_DISABLE_TELEMETRY=1
export HF_HUB_ENABLE_HF_TRANSFER=1
PY="$REPO_ROOT/.venv/bin/python"

ts() { date +%H:%M; }
# note() writes to the log and to STDERR — never stdout, so that
# `MP=$(fetch_model ...)` captures only the model path.
note() { echo "[$(ts)] $*" >> "$LOG"; echo "[$(ts)] $*" >&2; }
alert() { note "ALERT | $*"; }
decision() { note "DECYZJA | $*"; }

# summarise <dir> -> "passed/total"
summarise() {
  "$PY" - "$1" <<'PYEOF'
import json,sys,pathlib
p=pathlib.Path(sys.argv[1])/"summary.json"
try:
    d=json.loads(p.read_text())
    print(f"{d.get('num_passed','?')}/{d.get('num_tasks','?')}")
except Exception as e:
    print(f"ERR({e.__class__.__name__})")
PYEOF
}

# run_one PHASE MODEL_ID QUANT MODELPATH CHATFMT NCTX SUITELABEL TASKSDIR REPAIR(0|1) OUTDIR [SEEDS] [TEMP]
run_one() {
  local PHASE=$1 MID=$2 Q=$3 MPATH=$4 CFMT=$5 NCTX=$6 SLAB=$7 TDIR=$8 REP=$9 OUT=${10}
  local SEEDS=${11:-42} TEMP=${12:-0.0}
  local repflag="" replab="off"
  if [ "$REP" = "1" ]; then repflag="--repair"; replab="on"; fi
  if [ -f "$OUT/summary.json" ]; then
    note "$PHASE | $MID | $Q | $SLAB | $replab | $(summarise "$OUT") | SKIP(already done)"
    return 0
  fi
  mkdir -p "$OUT"
  local t0=$(date +%s)
  cd "$REPO_ROOT"
  "$PY" -m polagentbench.cli run-suite \
      --model-path "$MPATH" --model-id "$MID" --quant "$Q" \
      --tasks-dir "$TDIR" --seeds "$SEEDS" --temperature "$TEMP" \
      --n-ctx "$NCTX" --chat-format "$CFMT" \
      $repflag --output "$OUT" > "$OUT/run.log" 2>&1
  local rc=$?
  local el=$(( ($(date +%s) - t0 + 30) / 60 ))
  if [ $rc -ne 0 ]; then
    alert "$PHASE | $MID | $Q | $SLAB | $replab | rc=$rc — run failed, skipped. tail: $(tail -3 "$OUT/run.log" | tr '\n' ' ')"
    return 1
  fi
  note "$PHASE | $MID | $Q | $SLAB | $replab | $(summarise "$OUT") | ${el}min"
  return 0
}

# fetch_model REPO FILENAME  -> echoes local path
fetch_model() {
  local R=$1 F=$2
  if [ ! -f "$REPO_ROOT/models/$F" ]; then
    note "download | $R | $F"
    "$REPO_ROOT/.venv/bin/hf" download "$R" "$F" --local-dir "$REPO_ROOT/models" >/dev/null 2>&1 \
      || { alert "download FAILED $R/$F"; return 1; }
  fi
  df -h / | tail -1 >> "$LOG"
  echo "$REPO_ROOT/models/$F"
}

# wait_for_scp TAG — block until the orchestrator confirms results are safely off-box
wait_for_scp() {
  local TAG=$1
  touch "$FLAGS/done_$TAG"
  note "waiting for scp ack: $TAG"
  local w=0
  while [ ! -f "$FLAGS/ok_$TAG" ]; do sleep 10; w=$((w+10));
    if [ $w -ge 3600 ]; then alert "scp ack timeout 60min for $TAG — keeping model, continuing"; return 1; fi
  done
  return 0
}
