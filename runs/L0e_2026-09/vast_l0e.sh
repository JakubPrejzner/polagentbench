#!/usr/bin/env bash
# L0e rerun on Vast (audit 2026-09-07, step 1): the extended-ladder L0 rung re-run with an explicit
# no-tool sentence in the prompt (tasks/ladder_l0e), plus an environment control: after each model load the
# ORIGINAL L0 tasks (tasks/ladder_l0_control, byte-identical copies of tasks/ladder_ext/v3_ext_L0_*.yaml)
# are run in the same session, so prompt effect (L0 vs L0e) and box effect (control vs release_data) separate.
# Scope fixed by the author on 2026-09-07, precisions whose GGUF files are reproducible bit for bit:
#   bielik-11b-v3          Q8_0 Q4_K_M   chatml   repair off/on
#   bielik-minitron-7b-v3  Q8_0 Q4_K_M   chatml   repair off/on
# The original L0 matrix (2026-07-29) also had 11B Q3_K_M/Q2_K, 7B Q3_K_M/Q2_K (requantized on the box,
# files and quantizer build unrecorded) and PLLuM at six precisions; those cells are not rerun.
# seeds 42, T = 0.0, n_ctx 8192, top_p 1.0, max_tokens 512 (CLI defaults), full GPU offload,
# llama-cpp-python 0.3.19 prebuilt cu124 wheel (its vendored llama.cpp is c0159f9).
# 8 L0e runs + 8 control runs x 10 tasks. One GGUF on disk at a time: the previous file is deleted and free
# space is checked before every download (32 GB overlay).
#
# Usage on the box:   bash runs/L0e_2026-09/vast_l0e.sh setup   # venv, wheel, ENV.txt, pytest (no models)
#                     bash runs/L0e_2026-09/vast_l0e.sh list    # print the run list and exit
#                     bash runs/L0e_2026-09/vast_l0e.sh run     # the 16 runs
#                     bash runs/L0e_2026-09/vast_l0e.sh all
# Pre-condition: the repository (branch fix/audit-2026-09-07) unpacked at $REPO_ROOT.
set -uo pipefail

REPO_ROOT=${REPO_ROOT:-/workspace/polagentbench}
OUTROOT="$REPO_ROOT/results/L0e_2026-09"
CTLROOT="$REPO_ROOT/results/L0_control_2026-09"
LOG="$OUTROOT/L0E_LOG.txt"
TASKS="tasks/ladder_l0e"
CTL_TASKS="tasks/ladder_l0_control"
PY="$REPO_ROOT/.venv/bin/python"
HF="$REPO_ROOT/.venv/bin/hf"
MODELS="$REPO_ROOT/models"
MARGIN_GB=2

mkdir -p "$OUTROOT" "$CTLROOT" "$MODELS"
note()  { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG" >&2; }
stop()  { note "STOP | $*"; exit 2; }

# Expected sha256 (Hugging Face LFS metadata, read 2026-09-07) and size in GB of the public GGUF files.
declare -A SHA=(
  [speakleash.Bielik-11B-v3.0-Instruct.Q8_0.gguf]=e807522649ba4f0fbcb729ea63336e59e515a162f57c7af31ac399c7f3cb4ab1
  [speakleash.Bielik-11B-v3.0-Instruct.Q4_K_M.gguf]=5b4e4dad195459bb2b40e1dacab6da49a70b8e04248d391987711758654147fa
  [minitron-Bielik-7B-v3.0-Instruct-GGUF.Q8_0.gguf]=8154b315c3637b1bcebe7cb76e30c4219ccb4fae3ec5596eed8bdc14b3b39bd2
  [minitron-Bielik-7B-v3.0-Instruct-GGUF.Q4_K_M.gguf]=0c1475426645924970b9ed1383df1ce89c47b991e7b78ce9a12d3fde94455b16
)
declare -A SIZE_GB=(
  [speakleash.Bielik-11B-v3.0-Instruct.Q8_0.gguf]=12
  [speakleash.Bielik-11B-v3.0-Instruct.Q4_K_M.gguf]=7
  [minitron-Bielik-7B-v3.0-Instruct-GGUF.Q8_0.gguf]=8
  [minitron-Bielik-7B-v3.0-Instruct-GGUF.Q4_K_M.gguf]=5
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
      for SUITE in L0e L0ctl; do
        for REP in no_repair repair; do n=$((n+1)); printf '%2d  %-22s %-7s %-6s %-9s %s\n' "$n" "$MID" "$Q" "$SUITE" "$REP" "$P.$Q.gguf"; done
      done
    done
  done
  echo "total runs: $n  (8 x $TASKS + 8 x $CTL_TASKS, 10 tasks each)"
}

record_sha() {  # record_sha <file>: verify against SHA[] (rule 4: stop on mismatch)
  local f=$1 b got exp
  b=$(basename "$f"); got=$(sha256sum "$f" | cut -d' ' -f1); exp=${SHA[$b]:-}
  echo "$got  $b" >> "$OUTROOT/GGUF_SHA256.txt"
  [ -z "$exp" ] && stop "no reference sha256 for $b (outside the approved scope)"
  [ "$got" != "$exp" ] && stop "sha256 mismatch for $b: expected $exp got $got"
  note "sha256 OK | $b | $got (matches HF LFS)"
}

free_gb() { df --output=avail -B1G / | tail -1 | tr -d ' '; }

ensure_space() {  # ensure_space <file>: delete any leftover GGUF, then require size + margin free
  local b=$1 need avail
  for old in "$MODELS"/*.gguf; do [ -f "$old" ] && { note "delete previous model | $(basename "$old")"; rm -f "$old"; }; done
  need=$(( ${SIZE_GB[$b]:-13} + MARGIN_GB )); avail=$(free_gb)
  note "disk check | need ${need} GB for $b | free ${avail} GB"
  [ "$avail" -ge "$need" ] || stop "not enough disk for $b: need ${need} GB, free ${avail} GB"
}

fetch_model() {  # fetch_model <hf-repo> <file>  -> prints local path
  local R=$1 F=$2
  if [ ! -f "$MODELS/$F" ]; then
    ensure_space "$F"
    note "download | $R | $F"
    "$HF" download "$R" "$F" --local-dir "$MODELS" >/dev/null 2>&1 || stop "download failed $R/$F"
  fi
  record_sha "$MODELS/$F"
  df -h / | tail -1 >> "$LOG"
  echo "$MODELS/$F"
}

run_one() {  # run_one <model-id> <quant> <model-path> <chat-format> <repair 0|1> <tag> <outroot> <tasksdir>
  local MID=$1 Q=$2 MP=$3 CFMT=$4 REP=$5 TAG=$6 ROOT=$7 TDIR=$8 repflag="" replab="no_repair"
  [ "$REP" = "1" ] && { repflag="--repair"; replab="repair"; }
  local OUT="$ROOT/${TAG}_${replab}"
  if [ -f "$OUT/summary.json" ]; then note "SKIP (done) | $MID | $Q | $TDIR | $replab"; return 0; fi
  mkdir -p "$OUT"; local t0=$(date +%s)
  ( cd "$REPO_ROOT" && "$PY" -m polagentbench.cli run-suite \
      --model-path "$MP" --model-id "$MID" --quant "$Q" \
      --tasks-dir "$TDIR" --seeds 42 --temperature 0.0 \
      --n-ctx 8192 --chat-format "$CFMT" $repflag --output "$OUT" > "$OUT/run.log" 2>&1 )
  local rc=$?
  if [ $rc -ne 0 ]; then note "ALERT | $MID | $Q | $TDIR | $replab | rc=$rc | $(tail -2 "$OUT/run.log" | tr '\n' ' ')"; return 1; fi
  note "DONE | $MID | $Q | $TDIR | $replab | $("$PY" -c "import json;d=json.load(open('$OUT/summary.json'));print(d['num_passed'],'/',d['num_tasks'])") | $(( $(date +%s) - t0 ))s"
}

setup() {
  cd "$REPO_ROOT" || stop "repo missing at $REPO_ROOT"
  note "=== SETUP ==="
  uv venv --python 3.12 .venv >/dev/null 2>&1 || stop "uv venv failed"
  # prebuilt cu124 wheel (as in the original run), then the project on top of it.
  # Installing via --index-url resolved to the CPU build on this box (no libggml-cuda.so, gpu_offload False),
  # so the wheel is fetched by its exact URL from the cu124 index, hashed, and installed with --no-deps.
  uv pip install --python "$PY" -e . huggingface_hub pytest || stop "project install failed"
  mkdir -p /workspace/wheels
  WHL_URL="https://github.com/abetlen/llama-cpp-python/releases/download/v0.3.19-cu124/llama_cpp_python-0.3.19-cp312-cp312-linux_x86_64.whl"
  WHL=/workspace/wheels/llama_cpp_python-0.3.19-cp312-cp312-linux_x86_64.whl
  [ -f "$WHL" ] || curl -sL -o "$WHL" "$WHL_URL" || stop "wheel download failed"
  uv pip install --python "$PY" --force-reinstall --no-deps "$WHL" || stop "wheel install failed"
  "$PY" -c "import llama_cpp; print('llama_cpp', llama_cpp.__version__, 'gpu_offload', llama_cpp.llama_supports_gpu_offload())" | tee -a "$LOG"
  "$PY" -c "import llama_cpp,sys; sys.exit(0 if llama_cpp.llama_supports_gpu_offload() else 1)" || stop "wheel has no GPU offload"
  {
    echo "date: $(date -u +%FT%TZ)"
    echo "repo: $(cat "$REPO_ROOT/RELEASE_COMMIT.txt" 2>/dev/null || echo 'see FIX_REPORT')"
    echo "tasks sha256:"; sha256sum tasks/ladder_l0e/*.yaml tasks/ladder_l0e/SHA256SUMS.txt tasks/ladder_l0_control/*.yaml
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader; nvidia-smi | grep -oE 'CUDA Version: [0-9.]+'
    uname -a; "$PY" --version
    "$PY" -m pip freeze 2>/dev/null | grep -iE "llama|numpy|pydantic|yaml|diskcache|jinja|huggingface"
    echo "llama-cpp-python wheel: $WHL_URL"; echo "wheel sha256: $(sha256sum "$WHL" | cut -d' ' -f1)"
    echo "llama.cpp vendored in llama-cpp-python v0.3.19: c0159f9c1f874da15e94f371d136f5920b4b5335"
  } > "$OUTROOT/ENV.txt"
  nvidia-smi > "$OUTROOT/nvidia-smi.txt"
  ( cd "$REPO_ROOT" && "$PY" -m pytest -q 2>&1 | tail -1 ) | tee "$OUTROOT/pytest.txt" | tee -a "$LOG"
  note "=== SETUP DONE ==="
}

run() {
  cd "$REPO_ROOT" || stop "repo missing"
  note "=== RUN START | L0e + L0 control | manifests $(sha256sum tasks/ladder_l0e/SHA256SUMS.txt | cut -c1-12) $(sha256sum tasks/ladder_l0_control/SHA256SUMS.txt | cut -c1-12) ==="
  list_runs | tee -a "$LOG"
  for ROW in "${MATRIX[@]}"; do
    IFS='|' read -r MID R P CFMT QS <<< "$ROW"
    for E in $QS; do
      Q=${E%%:*}; T=${E##*:}
      MP=$(fetch_model "$R" "$P.$Q.gguf") || exit 2
      run_one "$MID" "$Q" "$MP" "$CFMT" 0 "$T" "$OUTROOT" "$TASKS"
      run_one "$MID" "$Q" "$MP" "$CFMT" 1 "$T" "$OUTROOT" "$TASKS"
      run_one "$MID" "$Q" "$MP" "$CFMT" 0 "$T" "$CTLROOT" "$CTL_TASKS"
      run_one "$MID" "$Q" "$MP" "$CFMT" 1 "$T" "$CTLROOT" "$CTL_TASKS"
      note "delete model | $(basename "$MP")"; rm -f "$MP"
    done
  done
  note "=== RUN DONE | L0e dirs: $(ls -d "$OUTROOT"/*_repair "$OUTROOT"/*_no_repair 2>/dev/null | wc -l) | control dirs: $(ls -d "$CTLROOT"/*_repair "$CTLROOT"/*_no_repair 2>/dev/null | wc -l) ==="
  ( cd "$REPO_ROOT/results" && tar czf L0e_2026-09.tgz L0e_2026-09 L0_control_2026-09 && sha256sum L0e_2026-09.tgz | tee -a "$LOG" )
}

case "${1:-all}" in
  setup) setup ;;
  list)  list_runs ;;
  run)   run ;;
  all)   setup && run ;;
  *) echo "usage: $0 setup|list|run|all"; exit 1 ;;
esac
