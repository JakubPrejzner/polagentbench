"""Verify each structural twin and its _arith partner share prompt + tool chain.

The only legitimate difference is the _arith twin's extra final_answer_contains_any.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.stdout.reconfigure(encoding="utf-8")
from polagentbench.io import load_task

ADV = Path(__file__).resolve().parent.parent / "tasks" / "adversarial"
PAIRS = ["001", "004", "005", "006", "007", "010"]
EN_PAIRS = ["en_001", "en_003", "en_005"]

def chain(t):
    return t.expected_final_state.get("tools_called_in_order_strict")

ok = True
for stem in PAIRS + EN_PAIRS:
    twin = load_task(ADV / f"v3_chain_{stem}.yaml")
    arith = load_task(ADV / f"v3_chain_{stem}_arith.yaml")
    same_prompt = twin.prompt == arith.prompt
    same_chain = chain(twin) == chain(arith)
    same_tools = twin.available_tools == arith.available_tools
    good = same_prompt and same_chain and same_tools
    ok = ok and good
    fc = next((c["args"] for c in chain(arith) if c["tool"] == "get_forecast"), None)
    print(f"{stem:<8} prompt={'=' if same_prompt else 'DIFF'} chain={'=' if same_chain else 'DIFF'} "
          f"tools={'=' if same_tools else 'DIFF'} fc={fc} golden={arith.expected_final_state.get('final_answer_contains_any')} "
          f"-> {'OK' if good else 'MISMATCH'}")

print("\nALL PAIRS MATCHED" if ok else "\nPAIR MISMATCH!")
sys.exit(0 if ok else 1)
