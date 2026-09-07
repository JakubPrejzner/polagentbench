#!/usr/bin/env bash
# L0e rerun on Vast (audit 2026-09-07, step 1): the extended-ladder L0 rung re-run with an explicit
# no-tool sentence in the prompt (tasks/ladder_l0e), on the precisions whose GGUF files are reproducible
# bit for bit (public Hugging Face files with LFS sha256). Scope fixed by the author on 2026-09-07:
#   bielik-11b-v3          Q8_0 Q4_K_M   chatml   repair off/on
#   bielik-minitron-7b-v3  Q8_0 Q4_K_M   chatml   repair off/on
# Dropped from the original ladder matrix: 7B Q3_K_M/Q2_K (requantized on the box in July, files and the
# quantizer build not recorded), 11B Q3_K_M/Q2_K and PLLuM (out of the approved scope).
# seeds 42, T = 0.0, n_ctx 8192, top_p 1.0, max_tokens 512 (CLI defaults), full GPU offload,
# llama-cpp-python 0.3.19 prebuilt cu124 wheel (its vendored llama.cpp is c0159f9).
# 8 runs x 10 tasks. Models are fetched one at a time and deleted after use (32 GB overlay).
#
# Usage on the box:   bash runs/L0e_2026-09/vast_l0e.sh setup   # venv, wheel, ENV.txt, pytest (no models)
#                     bash runs/L0e_2026-09/vast_l0e.sh list    # print the run list and exit
#                     bash runs/L0e_2026-09/vast_l0e.sh run     # the 8 runs
#                     bash runs/L0e_2026-09/vast_l0e.sh all
# Pre-condition: the repository (branch fix/audit-2026-09-07) unpacked at $REPO_ROOT.
set -uo pipefail

REPO_ROOT=${REPO_ROOT:-/workspace/polagentbench}
OUTROOT="$REPO_ROOT/results/L0e_2026-09"
LOG="$OUTROOT/L0E_LOG.txt"
WHL_INDEX=${WHL_INDEX:-https://abetlen.github.io/llama-cpp-python/whl/cu124}
TASKS="tasks/ladder_l0e"
PY="$REPO_ROOT/.venv/bin/python"
HF="$REPO_ROOT/.venv/bin/hf"
MODELS="$REPO_ROOT/models"

mkdir -p "$OUTROOT" "$MODELS"
note()  { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG" >&2; }
stop()  { note "STOP | $*"; exit 2; }

# Expected sha256 of the public GGUF files (Hugging Face LFS metadata, read 2026-09-07).
declare -A SHA=(
  [speakleash.Bielik-11B-v3.0-Instruct.Q8_0.gguf]=e807522649ba4f0fbcb729ea63336e59e515a162f57c7af31ac399c7f3cb4ab1
  [speakleash.Bielik-11B-v3.0-Instruct.Q4_K_M.gguf]=5b4e4dad195459bb2b40e1dacab6da49a70b8e04248d391987711758654147fa
  [minitron-Bielik-7B-v3.0-Instruct-GGUF.Q8_0.gguf]=8154b315c3637b1bcebe7cb76e30c4219ccb4fae3ec5596eed8bdc14b3b39bd2
  [minitron-Bielik-7B-v3.0-Instruct-GGUF.Q4_K_M.gguf]=0c1475426645924970b9ed1383df1ce89c47b991e7b78ce9a12d3fde94455b16
)

# model-id | HF repo | file prefix | chat format | quant:tag list
MATRIX=(
  "bielik-11b-v3|DevQuasar/speakleash.Bielik-11B-v3.0-Instruct-GGUF|speakleash.Bielik-11B-v3.0-Instruct|chatml|Q8_0:11b_q8 Q4_K_M:11b_q4"
  "bielik-minitron-7b-v3|speakleash/Bielik-Minitron-7B-v3.0-Instruct-GGUF|minitron-Bielik-7B-v3.0-Instruct-GGUF|chatml|Q8_0:7b_q8 Q4_K_M:7b_q4"
)

list_runs() {
  local n=0
  for ROW in "${MATRIX[@]}"; do
    IFS='|' read -r MID R P CFMT QS <<< "$ROW"
    for E in $QS; do
      Q=${E%%:*}; T=${E##*:}
      for REP in no_repair repair; do n=$((n+1)); printf '%2d  %-22s %-7s %-9s %-7s %s\n' "$n" "$MID" "$Q" "$REP" "$CFMT" "$P.$Q.gguf"; done
    done
  done
  echo "total runs: $n  (x 10 tasks from $TASKS)"
}

record_sha() {  # record_sha <file>: verify against SHA[] (rule 4: stop on mismatch)
  local f=$1 b got exp
  b=$(basename "$f"); got=$(sha256sum "$f" | cut -d' ' -f1); exp=${SHA[$b]:-}
  echo "$got  $b" >> "$OUTROOT/GGUF_SHA256.txt"
  [ -z "$exp" ] && stop "no reference sha256 for $b (outside the approved scope)"
  [ "$got" != "$exp" ] && stop "sha256 mismatch for $b: expected $exp got $got"
  note "sha256 OK | $b | $got (matches HF LFS)"
}

fetch_model() {  # fetch_model <hf-repo> <file>  -> prints local path
  local R=$1 F=$2
  if [ ! -f "$MODELS/$F" ]; then
    note "download | $R | $F"
    "$HF" download "$R" "$F" --local-dir "$MODELS" >/dev/null 2>&1 || stop "download failed $R/$F"
  fi
  record_sha "$MODELS/$F"
  df -h / | tail -1 >> "$LOG"
  echo "$MODELS/$F"
}

run_one() {  # run_one <model-id> <quant> <model-path> <chat-format> <repair 0|1> <tag>
  local MID=$1 Q=$2 MP=$3 CFMT=$4 REP=$5 TAG=$6 repflag="" replab="no_repair"
  [ "$REP" = "1" ] && { repflag="--repair"; replab="repair"; }
  local OUT="$OUTROOT/${TAG}_${replab}"
  if [ -f "$OUT/summary.json" ]; then note "SKIP (done) | $MID | $Q | $replab"; return 0; fi
  mkdir -p "$OUT"; local t0=$(date +%s)
  ( cd "$REPO_ROOT" && "$PY" -m polagentbench.cli run-suite \
      --model-path "$MP" --model-id "$MID" --quant "$Q" \
      --tasks-dir "$TASKS" --seeds 42 --temperature 0.0 \
      --n-ctx 8192 --chat-format "$CFMT" $repflag --output "$OUT" > "$OUT/run.log" 2>&1 )
  local rc=$?
  if [ $rc -ne 0 ]; then note "ALERT | $MID | $Q | $replab | rc=$rc | $(tail -2 "$OUT/run.log" | tr '\n' ' ')"; return 1; fi
  note "DONE | $MID | $Q | $replab | $("$PY" -c "import json;d=json.load(open('$OUT/summary.json'));print(d['num_passed'],'/',d['num_tasks'])") | $(( $(date +%s) - t0 ))s"
}

setup() {
  cd "$REPO_ROOT" || stop "repo missing at $REPO_ROOT"
  note "=== SETUP ==="
  uv venv --python 3.12 .venv >/dev/null 2>&1 || stop "uv venv failed"
  # prebuilt cu124 wheel first (as in the original run), then the project on top of it
  uv pip install --python "$PY" --index-url "$WHL_INDEX" --extra-index-url https://pypi.org/simple "llama-cpp-python==0.3.19" || stop "wheel install failed"
  uv pip install --python "$PY" -e . huggingface_hub pytest || stop "project install failed"
  "$PY" -c "import llama_cpp; print('llama_cpp', llama_cpp.__version__, 'gpu_offload', llama_cpp.llama_supports_gpu_offload())" | tee -a "$LOG"
  {
    echo "date: $(date -u +%FT%TZ)"
    echo "repo: $(cat "$REPO_ROOT/RELEASE_COMMIT.txt" 2>/dev/null || echo 'see FIX_REPORT')"
    echo "tasks sha256:"; sha256sum tasks/ladder_l0e/*.yaml tasks/ladder_l0e/SHA256SUMS.txt
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader; nvidia-smi | grep -oE 'CUDA Version: [0-9.]+'
    uname -a; "$PY" --version
    "$PY" -m pip freeze 2>/dev/null | grep -iE "llama|numpy|pydantic|yaml|diskcache|jinja|huggingface"
    "$PY" -c "import llama_cpp,os; p=os.path.dirname(llama_cpp.__file__); print('llama_cpp path', p)"
    echo "llama.cpp vendored in llama-cpp-python v0.3.19: c0159f9c1f874da15e94f371d136f5920b4b5335"
  } > "$OUTROOT/ENV.txt"
  nvidia-smi > "$OUTROOT/nvidia-smi.txt"
  ( cd "$REPO_ROOT" && "$PY" -m pytest -q 2>&1 | tail -1 ) | tee "$OUTROOT/pytest.txt" | tee -a "$LOG"
  note "=== SETUP DONE ==="
}

run() {
  cd "$REPO_ROOT" || stop "repo missing"
  note "=== RUN START | L0e | tasks manifest $(sha256sum tasks/ladder_l0e/SHA256SUMS.txt | cut -c1-12) ==="
  list_runs | tee -a "$LOG"
  for ROW in "${MATRIX[@]}"; do
    IFS='|' read -r MID R P CFMT QS <<< "$ROW"
    for E in $QS; do
      Q=${E%%:*}; T=${E##*:}
      MP=$(fetch_model "$R" "$P.$Q.gguf") || exit 2
      run_one "$MID" "$Q" "$MP" "$CFMT" 0 "$T"
      run_one "$MID" "$Q" "$MP" "$CFMT" 1 "$T"
      rm -f "$MP"
    done
  done
  note "=== RUN DONE | $(ls -d "$OUTROOT"/*_repair "$OUTROOT"/*_no_repair 2>/dev/null | wc -l) run dirs ==="
  ( cd "$REPO_ROOT/results" && tar czf L0e_2026-09.tgz L0e_2026-09 && sha256sum L0e_2026-09.tgz | tee -a "$LOG" )
}

case "${1:-all}" in
  setup) setup ;;
  list)  list_runs ;;
  run)   run ;;
  all)   setup && run ;;
  *) echo "usage: $0 setup|list|run|all"; exit 1 ;;
esac
