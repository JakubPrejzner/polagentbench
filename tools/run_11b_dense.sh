#!/usr/bin/env bash
# PolAgentBench — Bielik-11B-v3.0 DENSE quant curve (6 quants × repair off/on = 12 runs).
# PREPARED OFFLINE 2026-06-18 — DO NOT run yet; DO NOT modify pipeline code.
# Streaming disk management: download one quant -> smoke -> run both -> DELETE -> next.
# Peak disk ~14 GB (during Q8_0); fits a 54 GB box trivially. No F16, NO requantize:
# all 6 quants are ready-made (DevQuasar, single source = consistent static recipe).
#
# Quant SOURCE: DevQuasar/speakleash.Bielik-11B-v3.0-Instruct-GGUF (public, no token,
#   quantized from speakleash/Bielik-11B-v3.0-Instruct; Q4-Q8 sizes == official static).
#   Single source across the whole curve avoids a mid-curve quantizer discontinuity.
# Suite: UNCHANGED 67-task adversarial set @ commit 83db813 (model-agnostic).
# Pipeline: UNCHANGED — only CLI args differ from the 7B run.
set -euo pipefail

REPO="DevQuasar/speakleash.Bielik-11B-v3.0-Instruct-GGUF"
PREFIX="speakleash.Bielik-11B-v3.0-Instruct"
MODEL_ID="bielik-11b-v3"
RES="results/v3_11b_2026-06-18"
# tasks/ unchanged since 83db813; HEAD may be a023c3b (SESSION_LOG-only commit) or later.
# Stamp must equal the actually-synced HEAD, so derive it instead of hardcoding.
SUITE_COMMIT=$(git rev-parse --short HEAD)
# full quant label  ->  short output-dir tag
QUANTS=("Q8_0:q8" "Q6_K:q6" "Q5_K_M:q5" "Q4_K_M:q4" "Q3_K_M:q3" "Q2_K:q2")

cd /workspace/polagentbench
NVLIB=$(.venv/bin/python -c "import nvidia;print(list(nvidia.__path__)[0])")
export LD_LIBRARY_PATH="$NVLIB/cublas/lib:$NVLIB/cuda_runtime/lib:$NVLIB/cuda_nvrtc/lib"
export HF_HUB_DISABLE_TELEMETRY=1
mkdir -p models "$RES"

# Precondition gates (run once before the loop):
#   git rev-parse HEAD == 83db813 ; ls tasks/adversarial/*.yaml | wc -l == 67 ; uv run pytest -q == 204

for ENTRY in "${QUANTS[@]}"; do
  Q="${ENTRY%%:*}"; TAG="${ENTRY##*:}"
  F="models/${PREFIX}.${Q}.gguf"

  echo "===== $Q : download ====="
  .venv/bin/hf download "$REPO" "${PREFIX}.${Q}.gguf" --local-dir models
  df -h / | tail -1

  echo "===== $Q : coherence smoke (PL) — STOP if gibberish ====="
  .venv/bin/python - "$F" <<'PY'
import sys
from llama_cpp import Llama
llm = Llama(model_path=sys.argv[1], n_gpu_layers=-1, n_ctx=2048,
            verbose=False, chat_format="chatml", seed=42)
o = llm.create_chat_completion(
    messages=[{"role": "user", "content": "Jaka jest stolica Polski? Odpowiedz jednym krotkim zdaniem."}],
    max_tokens=64, temperature=0.0)
print("SMOKE:", o["choices"][0]["message"]["content"].strip())
PY

  for R in no_repair repair; do
    FLAG=""; [ "$R" = "repair" ] && FLAG="--repair"
    OUT="$RES/${TAG}_${R}"
    echo "===== $Q $R : run 67 (T=0/seed42) ====="
    .venv/bin/polagentbench run-suite \
      --model-path "$F" --model-id "$MODEL_ID" --quant "$Q" \
      --chat-format chatml --tasks-dir tasks/adversarial \
      --seeds 42 --temperature 0.0 $FLAG --output "$OUT"
    .venv/bin/python -c "import json;d=json.load(open('$OUT/summary.json'));print('$Q $R sr=',d['success_rate'],d['commit_hash'][:7]);assert d['commit_hash'][:7]=='$SUITE_COMMIT','COMMIT MISMATCH — STOP'"
  done

  # --- LOCAL side, after each quant: scp both dirs, verify, THEN allow delete ---
  #   scp -r -P <port> root@<host>:/workspace/polagentbench/$RES/${TAG}_no_repair \
  #          root@<host>:/workspace/polagentbench/$RES/${TAG}_repair  <local $RES>/
  echo "===== $Q : DELETE model (streaming; results dirs stay on box for scp) ====="
  rm -f "$F"
  df -h / | tail -1
done
echo "ALL 12 RUNS DONE."
# Sanity (no 11B baseline → not a reproduction): after Q8, easy-tier pass should be
# HIGH/plausible (>= ~0.8). If Q8 easy << 7B's 0.933 → suspect template/quant, investigate.
