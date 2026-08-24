#!/usr/bin/env bash
# FAZA 5 — wariancja przy probkowaniu. Bielik-11B, Q8_0 i Q3_K_M, T=0.7,
# seedy 1/2/3, main suite (67), repair OFF. 6 runow.
source /workspace/polagentbench/night/lib.sh

REPO="DevQuasar/speakleash.Bielik-11B-v3.0-Instruct-GGUF"
PREFIX="speakleash.Bielik-11B-v3.0-Instruct"
MID="bielik-11b-v3"
RESDIR="v3_11b_variance_2026-07-29"
cd "$REPO_ROOT"
note "=== FAZA5 START | $MID | main suite | T=0.7 | seedy 1,2,3 | repair off ==="

for E in "Q8_0:q8" "Q3_K_M:q3"; do
  Q="${E%%:*}"; TAG="${E##*:}"
  MP=$(fetch_model "$REPO" "${PREFIX}.${Q}.gguf") || { alert "FAZA5 | $Q pobranie nieudane, kwant pominiety"; continue; }
  for S in 1 2 3; do
    run_one FAZA5 "$MID" "$Q" "$MP" chatml 8192 "main-T0.7-seed$S" tasks/adversarial 0 \
            "results/$RESDIR/${TAG}_seed${S}" "$S" 0.7
  done
  wait_for_scp "${RESDIR}_${TAG}"
  if [ -f "$FLAGS/ok_${RESDIR}_${TAG}" ]; then
    rm -f "$MP"; rm -rf "$REPO_ROOT/models/.cache"
    note "FAZA5 | $Q | scp potwierdzony -> model skasowany | $(df -h / | tail -1 | awk '{print $4" wolne"}')"
  else
    alert "FAZA5 | $Q | brak potwierdzenia scp -> model ZOSTAJE"
  fi
done
note "=== FAZA5 DONE ==="
touch "$FLAGS/phase_done_FAZA5"
