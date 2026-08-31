#!/bin/bash
agent_model="local:Qwen3.6-35B-A3B"
attack_name="important_instructions"
defense_name="ipiguard"          # use "None" to run the original model (no defense)
suite_name="all"                 # expands to slack, banking, travel, workspace
mode="under_attack"              # "benign" for no-attack runs

output_dir="logs/"

mkdir -p "$output_dir"

python3 run/eval.py \
    --suite_name "$suite_name" \
    --agent_model "$agent_model" \
    --attack_name "$attack_name" \
    --defense_name "$defense_name" \
    --output_dir "$output_dir" \
    --mode "$mode"