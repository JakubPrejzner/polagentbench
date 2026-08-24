#!/usr/bin/env bash
# run_phase.sh — one model family, N quants, one suite, repair off+on.
# Streams: download -> 2 runs -> block for scp ack -> delete -> next quant.
#
# args: PHASE MODEL_ID REPO PREFIX CHATFMT RESDIR SUITELABEL TASKSDIR "Q8_0:q8 Q4_K_M:q4 ..."
source /workspace/polagentbench/night/lib.sh

PHASE=$1; MID=$2; REPO=$3; PREFIX=$4; CFMT=$5; RESDIR=$6; SLAB=$7; TDIR=$8; QUANTS=$9
cd "$REPO_ROOT"
note "=== $PHASE START | $MID | suite=$SLAB | kwanty: $QUANTS ==="

for ENTRY in $QUANTS; do
  Q="${ENTRY%%:*}"; TAG="${ENTRY##*:}"
  F="${PREFIX}.${Q}.gguf"
  MP=$(fetch_model "$REPO" "$F") || { alert "$PHASE | $Q | pobranie nieudane, kwant pominiety"; continue; }

  run_one "$PHASE" "$MID" "$Q" "$MP" "$CFMT" 8192 "$SLAB" "$TDIR" 0 "results/$RESDIR/${TAG}_no_repair"
  run_one "$PHASE" "$MID" "$Q" "$MP" "$CFMT" 8192 "$SLAB" "$TDIR" 1 "results/$RESDIR/${TAG}_repair"

  wait_for_scp "${RESDIR}_${TAG}"
  if [ -f "$FLAGS/ok_${RESDIR}_${TAG}" ]; then
    rm -f "$MP"; rm -rf "$REPO_ROOT/models/.cache"
    note "$PHASE | $Q | scp potwierdzony -> model skasowany | $(df -h / | tail -1 | awk '{print $4" wolne"}')"
  else
    alert "$PHASE | $Q | brak potwierdzenia scp -> model ZOSTAJE na dysku, ide dalej"
  fi
done
note "=== $PHASE DONE ==="
touch "$FLAGS/phase_done_$PHASE"
