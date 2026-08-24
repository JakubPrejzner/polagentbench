#!/usr/bin/env bash
# BONUS (nie z planu) — krzywa PLLuM-8B, 6 kwantow x {main 67, ladder 46} x {off,on} = 24 runy.
# Uruchamiana DOPIERO po zamknieciu faz 2-5, bo BRAMKA C byla NIEZDANA (0.400/0.467 < 0.5)
# i regula kazala FAZE 1 pominac. Te dane sa uzupelnieniem, nie realizacja planu.
# Kolejnosc kwantow wg promptu: Q8, Q4, Q2 (szkielet krzywej) potem Q6, Q5, Q3.
source /workspace/polagentbench/night/lib.sh

REPO="mradermacher/Llama-PLLuM-8B-instruct-GGUF"
PREFIX="Llama-PLLuM-8B-instruct"
MID="llama-pllum-8b"
CFMT="llama-3"
RESDIR="v3_pllum_2026-07-29"
cd "$REPO_ROOT"

w=0
while [ ! -f "$FLAGS/chain_done" ]; do sleep 30; w=$((w+30));
  if [ $w -ge 28800 ]; then alert "BONUS: chain nie skonczyl sie w 8h — bonus NIE startuje"; exit 0; fi
done

note "=== BONUS-PLLUM START (po zamknieciu planu; bramka C byla niezdana) ==="
mkdir -p "results/$RESDIR"
cat > "results/$RESDIR/BONUS_README.txt" <<'EOF'
UWAGA. Katalogi {q8,q6,q5,q4,q3,q2}_{main,ladder}_{no_repair,repair} w tym folderze
NIE sa realizacja FAZY 1 z planu nocnego. FAZA 1 zostala POMINIETA zgodnie z regula,
bo BRAMKA C wypadla ponizej progu: 0.400 (6/15) repair off, 0.467 (7/15) repair on,
przy progu 0.5. Dowody bramki sa w _gateC_q8_easy/ i _gateC_q8_easy_repair/.

Te runy zostaly dorzucone PO zamknieciu faz 2-5, z zapasu czasu, jako material
uzupelniajacy. Znany, udokumentowany defekt tego modelu na tym benchmarku:
PLLuM wymysla akcje najwyzszego poziomu ({"action":"send_weather_alert"} zamiast
{"action":"call_tool","tool":...}) i halucynuje sukces w final_answer przy pustym
final_state. Czytac z ta swiadomoscia.
EOF

for ENTRY in "Q8_0:q8" "Q4_K_M:q4" "Q2_K:q2" "Q6_K:q6" "Q5_K_M:q5" "Q3_K_M:q3"; do
  Q="${ENTRY%%:*}"; TAG="${ENTRY##*:}"
  MP=$(fetch_model "$REPO" "${PREFIX}.${Q}.gguf") || { alert "BONUS | $Q pobranie nieudane, kwant pominiety"; continue; }

  run_one BONUS-PLLUM "$MID" "$Q" "$MP" "$CFMT" 8192 main   tasks/adversarial 0 "results/$RESDIR/${TAG}_main_no_repair"
  run_one BONUS-PLLUM "$MID" "$Q" "$MP" "$CFMT" 8192 main   tasks/adversarial 1 "results/$RESDIR/${TAG}_main_repair"
  run_one BONUS-PLLUM "$MID" "$Q" "$MP" "$CFMT" 8192 ladder tasks/ladder_ext  0 "results/$RESDIR/${TAG}_ladder_no_repair"
  run_one BONUS-PLLUM "$MID" "$Q" "$MP" "$CFMT" 8192 ladder tasks/ladder_ext  1 "results/$RESDIR/${TAG}_ladder_repair"

  wait_for_scp "${RESDIR}_${TAG}"
  if [ -f "$FLAGS/ok_${RESDIR}_${TAG}" ]; then
    rm -f "$MP"; rm -rf "$REPO_ROOT/models/.cache"
    note "BONUS | $Q | scp potwierdzony -> model skasowany | $(df -h / | tail -1 | awk '{print $4" wolne"}')"
  else
    alert "BONUS | $Q | brak potwierdzenia scp -> model ZOSTAJE, przerywam bonus"
    break
  fi
done
note "=== BONUS-PLLUM DONE ==="
touch "$FLAGS/bonus_done"
