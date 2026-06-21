#!/bin/bash
agent_model="Qwen3-30B-A3B-Instruct-2507"
attack_name="important_instructions"
defense_name="ipiguard"          # use "None" to run the original model (no defense)
suite_name="travel"
mode="under_attack"              # "benign" for no-attack runs

# Root log dir. run/eval.py writes the AgentDojo tree underneath:
#   logs/{agent_model}[+{defense}]/{suite}/{user_task}/{attack_type}/{injection}.json
output_dir="logs"

mkdir -p "$output_dir"

# Full run by default (resumes / skips already-logged tasks).
# Add `--uid <id> --iid <id>` to debug a single task, or `--force_rerun` to redo.
python3 run/eval.py \
    --suite_name "$suite_name" \
    --agent_model "$agent_model" \
    --attack_name "$attack_name" \
    --defense_name "$defense_name" \
    --output_dir "$output_dir" \
    --mode "$mode"
