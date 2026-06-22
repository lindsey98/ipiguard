## 📖 Overview

IPIGuard evaluates LLM agents against **indirect prompt injection (IPI)** attacks on top of the
[AgentDojo](https://github.com/ethz-spylab/agentdojo) benchmark. Every evaluation is defined by three
choices:

- **Agent model** — the LLM that drives the agent. Can be a local open model served through an
  OpenAI-compatible endpoint (e.g. `Qwen3-30B-A3B-Instruct-2507`) or a hosted model
  (e.g. `gpt-4o-mini-2024-07-18`, `claude-sonnet-4-5-20250929`).
- **Attack** — the adversarial content injected into tool outputs (e.g. `important_instructions`), only
  active in `under_attack` mode.
- **Defense** — the defense strategy applied to the agent. Use `ipiguard` for the proposed defense, or
  `None` to run the **original model** with no defense.

This README walks through the four combinations of *(attack on / off)* × *(IPIGuard / original model)*
using the local **`Qwen3-30B-A3B-Instruct-2507`** as the agent model.


## 🔧 Installation

We recommend using Python ≥3.10.

```bash
# git clone
git clone https://github.com/lindsey98/ipiguard.git
cd ipiguard

# create conda environment
conda create -n ipiguard python=3.10
conda activate ipiguard

# install agentdojo (editable)
cd agentdojo
pip install -e .
cd ..
```


## 🔑 Setup

### Hosted models (optional)

Rename `.env.example` to `.env`, fill in the keys you need (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`,
`GOOGLE_API_KEY`), and load them:

```bash
set -a && source .env && set +a
```

### Local model (used by the examples below)

Serve your model with any OpenAI-compatible server. The examples use **Qwen3-30B-A3B-Instruct-2507**
on vLLM. The two tool-calling flags are important — they let vLLM parse the model's `<tool_call>`
output into native tool calls, which the **no-defense baseline** (`--defense_name None`) relies on:

```bash
CUDA_VISIBLE_DEVICES=4,5,6,7 \
vllm serve /path/to/Qwen3-30B-A3B-Instruct-2507 \
  --served-model-name Qwen3-30B-A3B-Instruct-2507 \
  --host 0.0.0.0 --port 8000 \
  --dtype bfloat16 \
  --enable-auto-tool-choice \
  --tool-call-parser hermes \
  --tensor-parallel-size 4 \
  --gpu-memory-utilization 0.92 \
  --max-model-len 131072
```

Then point IPIGuard at the server (defaults shown):

```bash
export LOCAL_BASE_URL=http://localhost:8000/v1
export LOCAL_API_KEY=EMPTY
```

The `--served-model-name` **must** match the `--agent_model` you pass to `run/eval.py`
(`Qwen3-30B-A3B-Instruct-2507`). Verify the endpoint is up with `curl $LOCAL_BASE_URL/models`.

> Other OpenAI-compatible servers (Ollama, SGLang, LM Studio, …) work too — just set `LOCAL_BASE_URL`
> to their `/v1` endpoint.


## 🚀 How to Run

Evaluations are launched with `run/eval.py`. The four scenarios differ only in the `--mode`,
`--attack_name`, and `--defense_name` arguments:

| Scenario                                  | `--mode`       | `--attack_name`          | `--defense_name` |
|-------------------------------------------|----------------|--------------------------|------------------|
| Important Instr. attack **+ IPIGuard**    | `under_attack` | `important_instructions` | `ipiguard`       |
| No attack **+ IPIGuard**                  | `benign`       | `important_instructions` | `ipiguard`       |
| Important Instr. attack **+ original model** | `under_attack` | `important_instructions` | `None`           |
| No attack **+ original model**            | `benign`       | `important_instructions` | `None`           |

In `benign` mode the attack is not injected, so `--attack_name` is ignored for utility — any valid value
(e.g. `important_instructions`) is fine. `--defense_name None` runs the **original model** with no defense.

All examples below use `--agent_model Qwen3-30B-A3B-Instruct-2507` and the `travel` suite. Swap
`--suite_name` for `workspace`, `slack`, `banking`, or `all`. To use a hosted model instead, just pass its
id (e.g. `--agent_model gpt-4o-mini-2024-07-18`) after setting the matching API key.

By default a run evaluates the **full** task set and **resumes** — it skips any task whose result JSON
already exists. Pass `--force_rerun` to re-execute, or `--uid`/`--iid` to debug a single task/injection.

### 1) Important Instr. attack + IPIGuard defense

```bash
python3 run/eval.py \
    --suite_name travel \
    --agent_model Qwen3-30B-A3B-Instruct-2507 \
    --attack_name important_instructions \
    --defense_name ipiguard \
    --mode under_attack \
    --output_dir logs
```

### 2) No attack + IPIGuard defense

```bash
python3 run/eval.py \
    --suite_name travel \
    --agent_model Qwen3-30B-A3B-Instruct-2507 \
    --attack_name important_instructions \
    --defense_name ipiguard \
    --mode benign \
    --output_dir logs
```

### 3) Important Instr. attack + original model (no defense)

```bash
python3 run/eval.py \
    --suite_name travel \
    --agent_model Qwen3-30B-A3B-Instruct-2507 \
    --attack_name important_instructions \
    --defense_name None \
    --mode under_attack \
    --output_dir logs
```

### 4) No attack + original model (no defense)

```bash
python3 run/eval.py \
    --suite_name travel \
    --agent_model Qwen3-30B-A3B-Instruct-2507 \
    --attack_name important_instructions \
    --defense_name None \
    --mode benign \
    --output_dir logs
```

### Using the shell script

`eval.sh` wraps a single configuration. Edit the variables at the top and run it:

```bash
# inside eval.sh
agent_model="Qwen3-30B-A3B-Instruct-2507"
attack_name="important_instructions"
defense_name="ipiguard"          # or "None" for the original model
suite_name="travel"
mode="under_attack"              # or "benign"
```

```bash
bash eval.sh
```

### Argument reference

| Argument          | Description                                                                                       |
|-------------------|---------------------------------------------------------------------------------------------------|
| `--agent_model`   | Agent model (e.g. `Qwen3-30B-A3B-Instruct-2507`, `Llama-3.3-70B-Instruct`, `gpt-4o-mini-2024-07-18`, `claude-sonnet-4-5-20250929`). |
| `--attack_name`   | Adversarial attack to simulate (e.g. `important_instructions`). Ignored in `benign` mode.          |
| `--defense_name`  | Defense strategy: `ipiguard` for the proposed defense, or `None` for the original (undefended) model. |
| `--suite_name`    | Task suite/domain: `travel`, `workspace`, `slack`, `banking`, or `all`.                            |
| `--mode`          | `benign` → standard tasks without attacks; `under_attack` → adversarial tasks with injected attacks. |
| `--output_dir`    | Root log directory (see [Outputs](#-outputs)).                                                     |
| `--uid` / `--iid` | **Debug only**: run a single user-task / injection-task id. Unset → run all tasks.                 |
| `--force_rerun`   | Re-run and overwrite tasks even if a result JSON already exists (default: resume / skip done).     |

Each run prints **ASR** (Attack Success Rate ↓, lower is better) and **Utility** (task success ↑,
higher is better) per suite and overall.


## 📂 Outputs

Results use AgentDojo's logging layout — one JSON per task under `--output_dir`:

```
logs/
└── Qwen3-30B-A3B-Instruct-2507+ipiguard/   # {agent_model}[+{defense}]
    └── banking/                            # suite
        └── user_task_0/                    # user task
            ├── none/none.json                              # benign run
            └── important_instructions/injection_task_0.json # under_attack run
```

Each JSON contains the full message trace plus `utility`, `security`, and — for IPIGuard runs — the DAG
details: `initial_dag`, `expanded_dag` (resolved args), an ordered `dag_events` timeline (node visits,
`<unknown>` arg resolutions, runtime-added tool calls), `new_tool_calls`, and token usage.


## 📌 Citation

```bibtex
@misc{an2025ipiguardnoveltooldependency,
      title={IPIGuard: A Novel Tool Dependency Graph-Based Defense Against Indirect Prompt Injection in LLM Agents},
      author={Hengyu An and Jinghuai Zhang and Tianyu Du and Chunyi Zhou and Qingming Li and Tao Lin and Shouling Ji},
      year={2025},
      eprint={2508.15310},
      archivePrefix={arXiv},
      primaryClass={cs.CR},
      url={https://arxiv.org/abs/2508.15310},
}
```


## 🏷️ License

Apache License 2.0 - See [LICENSE](LICENSE) for details.
