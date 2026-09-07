#!/usr/bin/env bash
# L0e rerun on Vast (audit 2026-09-07, step 1): the extended-ladder L0 rung re-run with an explicit
# no-tool sentence in the prompt (tasks/ladder_l0e), same matrix as the original ladder runs of
# 2026-07-29 (release_data/NIGHT_LOG.txt, release_data/night_scripts/*.sh):
#   bielik-11b-v3          Q8_0 Q4_K_M Q3_K_M Q2_K            chatml   repair off/on
#   bielik-minitron-7b-v3  Q8_0 Q3_K_M(req) Q2_K(req) Q4_K_M chatml   repair off/on
#   llama-pllum-8b         Q8_0 Q6_K Q5_K_M Q4_K_M Q3_K_M Q2_K llama-3 repair off/on
# seeds 42, T = 0.0, n_ctx 8192, top_p 1.0, max_tokens 512 (CLI defaults), full GPU offload.
# 28 runs x 10 tasks. Models are fetched one at a time and deleted after use (32 GB overlay).
#
# Usage on the box:   bash runs/L0e_2026-09/vast_l0e.sh setup     # venv, wheel, llama-quantize, ENV.txt, pytest
#                     bash runs/L0e_2026-09/vast_l0e.sh run       # the 28 runs
#                     bash runs/L0e_2026-09/vast_l0e.sh all
# Pre-conditions: the repository (branch fix/audit-2026-09-07) unpacked at $REPO_ROOT.
# NOT executed until the author approves the pre-flight report.
set -uo pipefail

REPO_ROOT=${REPO_ROOT:-/workspace/polagentbench}
OUTROOT="$REPO_ROOT/results/L0e_2026-09"
LOG="$OUTROOT/L0E_LOG.txt"
# vendor/llama.cpp submodule commit of llama-cpp-python v0.3.19 (GitHub API, checked 2026-09-07).
# The original night log records only "llama-quantize built CPU-only (GGML_CUDA=OFF, LLAMA_CURL=OFF)"
# without a commit; this is the closest documented choice and is recorded in ENV.txt.
LLAMACPP_COMMIT=${LLAMACPP_COMMIT:-c0159f9c1f874da15e94f371d136f5920b4b5335}
WHL_INDEX=${WHL_INDEX:-https://abetlen.github.io/llama-cpp-python/whl/cu124}
LLAMACPP_SRC=/workspace/llamacpp_src
QUANTIZE="$LLAMACPP_SRC/build/bin/llama-quantize"
TASKS="tasks/ladder_l0e"
PY="$REPO_ROOT/.venv/bin/python"
HF="$REPO_ROOT/.venv/bin/hf"
MODELS="$REPO_ROOT/models"

mkdir -p "$OUTROOT" "$MODELS"
note()  { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG" >&2; }
stop()  { note "STOP | $*"; exit 2; }

# Expected sha256 of the public GGUF files (Hugging Face LFS metadata, read 2026-09-07).
# The 7B Q3_K_M and Q2_K files are requantized locally and have no reference hash; theirs are recorded only.
declare -A SHA=(
  [speakleash.Bielik-11B-v3.0-Instruct.Q8_0.gguf]=e807522649ba4f0fbcb729ea63336e59e515a162f57c7af31ac399c7f3cb4ab1
  [speakleash.Bielik-11B-v3.0-Instruct.Q4_K_M.gguf]=5b4e4dad195459bb2b40e1dacab6da49a70b8e04248d391987711758654147fa
  [speakleash.Bielik-11B-v3.0-Instruct.Q3_K_M.gguf]=8389c373139861ab9374b65d9abdcf177aa352e58dbc2ff73b6e267a187ccbe7
  [speakleash.Bielik-11B-v3.0-Instruct.Q2_K.gguf]=891e4c4ee5afa3c3142ce6fb05a780f906822b8fc94a59be3ced4b1bafcd0442
  [minitron-Bielik-7B-v3.0-Instruct-GGUF.Q8_0.gguf]=8154b315c3637b1bcebe7cb76e30c4219ccb4fae3ec5596eed8bdc14b3b39bd2
  [minitron-Bielik-7B-v3.0-Instruct-GGUF.Q4_K_M.gguf]=0c1475426645924970b9ed1383df1ce89c47b991e7b78ce9a12d3fde94455b16
  [Llama-PLLuM-8B-instruct.Q8_0.gguf]=b8b2ae9e7323db5e968d73c191c677459c7e6a8952ec21d200db427a5a37b5cc
  [Llama-PLLuM-8B-instruct.Q6_K.gguf]=6ac35744dd5c1ea594cf12b1daf601a09dd4e59e7e6df0bf635e5bc4af886617
  [Llama-PLLuM-8B-instruct.Q5_K_M.gguf]=921278b4386b39bf927a79c59b79b6007c62c4afb4ad12e2ef231e63c7b81fda
  [Llama-PLLuM-8B-instruct.Q4_K_M.gguf]=4ae92e8e4a0cad1f32dc2baf706581267597aa83811b9dc1d6c6437b1695d28c
  [Llama-PLLuM-8B-instruct.Q3_K_M.gguf]=aa34a5b0a2972feb6c9608a75c885630adff3f54676e6b1c7c2bd530e01329a1
  [Llama-PLLuM-8B-instruct.Q2_K.gguf]=9ba65b322fc6b3430a34fdaa092e134da5b4b37cb896d6eb3e5d37bdf1473274
)

record_sha() {  # record_sha <file> ; verifies against SHA[] when a reference exists (rule 4: stop on mismatch)
  local f=$1 b got exp
  b=$(basename "$f"); got=$(sha256sum "$f" | cut -d' ' -f1); exp=${SHA[$b]:-}
  echo "$got  $b" >> "$OUTROOT/GGUF_SHA256.txt"
  if [ -n "$exp" ] && [ "$got" != "$exp" ]; then stop "sha256 mismatch for $b: expected $exp got $got"; fi
  note "sha256 OK | $b | $got${exp:+ (matches HF LFS)}"
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

pair() { run_one "$1" "$2" "$3" "$4" 0 "$5"; run_one "$1" "$2" "$3" "$4" 1 "$5"; }

setup() {
  cd "$REPO_ROOT" || stop "repo missing at $REPO_ROOT"
  note "=== SETUP | $(git rev-parse --short HEAD 2>/dev/null || echo 'no-git') ==="
  uv venv --python 3.12 .venv >/dev/null 2>&1 || stop "uv venv failed"
  # prebuilt cu124 wheel first (as in the original run), then the project on top of it
  uv pip install --python "$PY" --index-url "$WHL_INDEX" --extra-index-url https://pypi.org/simple "llama-cpp-python==0.3.19" || stop "wheel install failed"
  uv pip install --python "$PY" -e . huggingface_hub pytest || stop "project install failed"
  "$PY" -c "import llama_cpp,sys; print('llama_cpp', llama_cpp.__version__, 'gpu_offload', llama_cpp.llama_supports_gpu_offload())" | tee -a "$LOG"
  if [ ! -x "$QUANTIZE" ]; then
    git clone -q https://github.com/ggml-org/llama.cpp "$LLAMACPP_SRC" || stop "llama.cpp clone failed"
    git -C "$LLAMACPP_SRC" checkout -q "$LLAMACPP_COMMIT" || stop "cannot check out llama.cpp commit $LLAMACPP_COMMIT"
    cmake -S "$LLAMACPP_SRC" -B "$LLAMACPP_SRC/build" -DGGML_CUDA=OFF -DLLAMA_CURL=OFF -DCMAKE_BUILD_TYPE=Release >/dev/null 2>&1 \
      && cmake --build "$LLAMACPP_SRC/build" --target llama-quantize -j"$(nproc)" >/dev/null 2>&1 || stop "llama-quantize build failed"
  fi
  {
    echo "date: $(date -u +%FT%TZ)"; echo "repo HEAD: $(git rev-parse HEAD 2>/dev/null)"
    echo "tasks sha256:"; sha256sum tasks/ladder_l0e/*.yaml
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader; nvidia-smi | grep -oE 'CUDA Version: [0-9.]+'
    uname -a; "$PY" --version; "$PY" -m pip freeze 2>/dev/null | grep -iE "llama|numpy|pydantic|yaml|diskcache|jinja"
    echo "llama.cpp (llama-quantize) commit: $(git -C "$LLAMACPP_SRC" rev-parse HEAD)"
    "$QUANTIZE" --help 2>&1 | head -2
  } > "$OUTROOT/ENV.txt"
  nvidia-smi > "$OUTROOT/nvidia-smi.txt"
  ( cd "$REPO_ROOT" && "$PY" -m pytest -q 2>&1 | tail -1 ) | tee "$OUTROOT/pytest.txt" | tee -a "$LOG"
  note "=== SETUP DONE ==="
}

run() {
  cd "$REPO_ROOT" || stop "repo missing"
  note "=== RUN START | L0e | $(sha256sum tasks/ladder_l0e/SHA256SUMS.txt | cut -c1-12) ==="
  # --- Bielik-11B-v3 ---
  local R="DevQuasar/speakleash.Bielik-11B-v3.0-Instruct-GGUF" P="speakleash.Bielik-11B-v3.0-Instruct"
  for E in Q8_0:q8 Q4_K_M:q4 Q3_K_M:q3 Q2_K:q2; do
    Q=${E%%:*}; T=${E##*:}; MP=$(fetch_model "$R" "$P.$Q.gguf") || exit 2
    pair bielik-11b-v3 "$Q" "$MP" chatml "11b_$T"; rm -f "$MP"
  done
  # --- Bielik-Minitron-7B-v3: Q8_0 public, Q3_K_M/Q2_K requantized from Q8_0, Q4_K_M public ---
  R="speakleash/Bielik-Minitron-7B-v3.0-Instruct-GGUF"; P="minitron-Bielik-7B-v3.0-Instruct-GGUF"
  Q8=$(fetch_model "$R" "$P.Q8_0.gguf") || exit 2
  pair bielik-minitron-7b-v3 Q8_0 "$Q8" chatml 7b_q8
  [ -x "$QUANTIZE" ] || stop "llama-quantize missing"
  for E in Q3_K_M:q3 Q2_K:q2; do
    Q=${E%%:*}; T=${E##*:}; OUT="$MODELS/$P.$Q.gguf"
    note "requantize | Q8_0 -> $Q"
    "$QUANTIZE" --allow-requantize "$Q8" "$OUT" "$Q" > "$OUTROOT/requant_$T.log" 2>&1 || stop "requantize $Q failed"
    record_sha "$OUT"; pair bielik-minitron-7b-v3 "$Q" "$OUT" chatml "7b_$T"; rm -f "$OUT"
  done
  rm -f "$Q8"
  MP=$(fetch_model "$R" "$P.Q4_K_M.gguf") || exit 2; pair bielik-minitron-7b-v3 Q4_K_M "$MP" chatml 7b_q4; rm -f "$MP"
  # --- Llama-PLLuM-8B ---
  R="mradermacher/Llama-PLLuM-8B-instruct-GGUF"; P="Llama-PLLuM-8B-instruct"
  for E in Q8_0:q8 Q6_K:q6 Q5_K_M:q5 Q4_K_M:q4 Q3_K_M:q3 Q2_K:q2; do
    Q=${E%%:*}; T=${E##*:}; MP=$(fetch_model "$R" "$P.$Q.gguf") || exit 2
    pair llama-pllum-8b "$Q" "$MP" llama-3 "pllum_$T"; rm -f "$MP"
  done
  note "=== RUN DONE | $(ls -d "$OUTROOT"/*_repair "$OUTROOT"/*_no_repair 2>/dev/null | wc -l) run dirs ==="
  ( cd "$REPO_ROOT/results" && tar czf L0e_2026-09.tgz L0e_2026-09 && sha256sum L0e_2026-09.tgz | tee -a "$LOG" )
}

case "${1:-all}" in
  setup) setup ;;
  run)   run ;;
  all)   setup && run ;;
  *) echo "usage: $0 setup|run|all"; exit 1 ;;
esac
