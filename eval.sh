#!/bin/bash
agent_model="local:Llama-3.3-70b-instruct"
attack_name="important_instructions"
defense_name="ipiguard"          # use "None" to run the original model (no defense)
suite_name="travel"
mode="under_attack"              # "benign" for no-attack runs

output_dir="logs/$(echo $suite_name | tr '/' '_')/$(echo $agent_model | tr '/' '_')/$(echo $mode | tr '/' '_')_$(echo $attack_name | tr ' ' '_')_$(echo $defense_name | tr ' ' '_')_$(date +%Y%m%d_%H%M%S)"

mkdir -p "$output_dir"

python3 run/eval.py \
    --suite_name "$suite_name" \
    --agent_model "$agent_model" \
    --attack_name "$attack_name" \
    --defense_name "$defense_name" \
    --output_dir "$output_dir" \
    --mode "$mode" \
    --uid 0 \
    --iid 0