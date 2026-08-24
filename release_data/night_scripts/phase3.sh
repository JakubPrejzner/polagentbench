#!/usr/bin/env bash
# FAZA 3 — Bielik-Minitron-7B, ladder_ext, 4 kwanty.
# Q8_0 i Q4_K_M sa publiczne; Q3_K_M i Q2_K powstaja przez requantize z Q8_0
# (recepta jak w oryginalnym runie 7B — parytet metodologiczny).
#
# Kolejnosc Q8 -> Q3 -> Q2 -> Q4 (nie Q8/Q4/Q3/Q2), bo Q8_0 jest ZRODLEM
# requantize i musi dozyc do konca obu derywatow. Wyniki identyczne.
source /workspace/polagentbench/night/lib.sh

REPO="speakleash/Bielik-Minitron-7B-v3.0-Instruct-GGUF"
PREFIX="minitron-Bielik-7B-v3.0-Instruct-GGUF"
MID="bielik-minitron-7b-v3"
RESDIR="v3_7b_ladder_2026-07-29"
QUANTIZE="/workspace/llamacpp_src/build/bin/llama-quantize"
cd "$REPO_ROOT"
note "=== FAZA3 START | $MID | suite=ladder | Q8_0, Q3_K_M(req), Q2_K(req), Q4_K_M ==="

Q8="$REPO_ROOT/models/${PREFIX}.Q8_0.gguf"

pair() {  # pair <quant> <tag> <modelpath>
  run_one FAZA3 "$MID" "$1" "$3" chatml 8192 ladder tasks/ladder_ext 0 "results/$RESDIR/${2}_no_repair"
  run_one FAZA3 "$MID" "$1" "$3" chatml 8192 ladder tasks/ladder_ext 1 "results/$RESDIR/${2}_repair"
  wait_for_scp "${RESDIR}_${2}"
}

# --- Q8_0 (public, also the requantize source) ---
fetch_model "$REPO" "${PREFIX}.Q8_0.gguf" >/dev/null || { alert "FAZA3 | Q8_0 pobranie nieudane — faza przerwana"; exit 1; }
pair Q8_0 q8 "$Q8"

# --- Q3_K_M and Q2_K by requantize from Q8_0 ---
if [ ! -x "$QUANTIZE" ]; then
  alert "FAZA3 | brak llama-quantize ($QUANTIZE) — Q3_K_M i Q2_K POMINIETE, lece do Q4_K_M"
else
  for E in "Q3_K_M:q3" "Q2_K:q2"; do
    Q="${E%%:*}"; TAG="${E##*:}"
    OUT="$REPO_ROOT/models/${PREFIX}.${Q}.gguf"
    if [ ! -f "$OUT" ]; then
      note "requantize | Q8_0 -> $Q"
      "$QUANTIZE" --allow-requantize "$Q8" "$OUT" "$Q" > "$REPO_ROOT/night/requant_${TAG}.log" 2>&1 \
        || { alert "FAZA3 | requantize $Q nieudany — kwant pominiety"; continue; }
      note "requantize OK | $Q | $(du -h "$OUT" | cut -f1) | $(df -h / | tail -1 | awk '{print $4" wolne"}')"
    fi
    pair "$Q" "$TAG" "$OUT"
    if [ -f "$FLAGS/ok_${RESDIR}_${TAG}" ]; then rm -f "$OUT"; note "FAZA3 | $Q | scp potwierdzony -> skasowany";
    else alert "FAZA3 | $Q | brak potwierdzenia scp -> plik ZOSTAJE"; fi
  done
fi

# Q8_0 no longer needed as a source
if [ -f "$FLAGS/ok_${RESDIR}_q8" ]; then rm -f "$Q8"; note "FAZA3 | Q8_0 | scp potwierdzony -> skasowany"; fi
rm -rf "$REPO_ROOT/models/.cache"

# --- Q4_K_M (public) ---
MP=$(fetch_model "$REPO" "${PREFIX}.Q4_K_M.gguf") || { alert "FAZA3 | Q4_K_M pobranie nieudane"; MP=""; }
if [ -n "$MP" ]; then
  pair Q4_K_M q4 "$MP"
  if [ -f "$FLAGS/ok_${RESDIR}_q4" ]; then rm -f "$MP"; rm -rf "$REPO_ROOT/models/.cache"; note "FAZA3 | Q4_K_M | scp potwierdzony -> skasowany"; fi
fi

note "=== FAZA3 DONE ==="
touch "$FLAGS/phase_done_FAZA3"
