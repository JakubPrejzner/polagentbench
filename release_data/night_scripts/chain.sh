#!/usr/bin/env bash
# Night chain: wait for FAZA2, then run FAZA3 -> FAZA4 -> FAZA5 back to back.
source /workspace/polagentbench/night/lib.sh
cd "$REPO_ROOT"

w=0
while [ ! -f "$FLAGS/phase_done_FAZA2" ]; do sleep 20; w=$((w+20));
  if [ $w -ge 21600 ]; then alert "CHAIN: FAZA2 nie skonczyla sie w 6h — startuje FAZA3 mimo to"; break; fi
done

bash night/phase3.sh

bash night/run_phase.sh FAZA4 bielik-minitron-7b-v3 \
  speakleash/Bielik-Minitron-7B-v3.0-Instruct-GGUF \
  minitron-Bielik-7B-v3.0-Instruct-GGUF chatml \
  v3_7b_grid_2026-07-29 main tasks/adversarial 'Q6_K:q6 Q5_K_M:q5'

bash night/phase5.sh

note "=== CHAIN 3-4-5 DONE ==="
touch "$FLAGS/chain_done"
