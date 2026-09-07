#!/bin/bash
model="local:Qwen3.6-35B-A3B"
suites="banking slack travel workspace"   # or: shopping github dailylife / all / agentdyn / everything
defense="ipiguard"                        # "None" for the original model, or "ipiguard"
attack="important_instructions"

# --- benign (no attack): drop --run-attack ---
python3 main.py "$model" \
    --suite $suites \
    --defense "$defense"

# --- under attack: add --run-attack --attack <name> ---
# python3 main.py "$model" \
#     --run-attack --attack "$attack" \
#     --suite $suites \
#     --defense "$defense"

# Output always goes under logs/. Add --html to also write a rendered <task>.html per trace.
# Debug a single task with -ut <id> (and -it <id> under attack).
