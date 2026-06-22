## 📖 Overview

**IPIGuard** evaluates LLM agents against **indirect prompt injection (IPI)** attacks on top of the
[AgentDojo](https://github.com/ethz-spylab/agentdojo) benchmark. Each run is defined by three choices:

- **Agent model** — local open model via an OpenAI-compatible endpoint (e.g. `Qwen3-30B-A3B-Instruct-2507`)
  or a hosted model (e.g. `gpt-4o-mini-2024-07-18`, `claude-sonnet-4-5-20250929`).
- **Attack** — adversarial content injected into tool outputs (e.g. `important_instructions`), only in `under_attack` mode.
- **Defense** — `ipiguard` for the proposed defense, or `None` for the original (undefended) model.


## 🔧 Installation

Python ≥3.10.

```bash
git clone https://github.com/lindsey98/ipiguard.git
cd ipiguard
conda create -n ipiguard python=3.10 && conda activate ipiguard
cd agentdojo && pip install -e . && cd ..
```


## 🔑 Setup

**Local model (used in the examples).** Serve it with any OpenAI-compatible server. The two tool-calling
flags let vLLM parse `<tool_call>` output into native tool calls (needed by the no-defense baseline):

```bash
vllm serve /path/to/Qwen3-30B-A3B-Instruct-2507 \
  --served-model-name Qwen3-30B-A3B-Instruct-2507 \
  --port 8000 --enable-auto-tool-choice --tool-call-parser hermes

export LOCAL_BASE_URL=http://localhost:8000/v1   # default
export LOCAL_API_KEY=EMPTY
```

`--served-model-name` must equal the `--agent_model` you pass below.

**Hosted models (optional).** Copy `.env.example` to `.env`, add keys (`OPENAI_API_KEY`,
`ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`), then `set -a && source .env && set +a`.


## 🚀 Run

One command, parameterized by `--mode` / `--defense_name`:

```bash
python3 run/eval.py \
    --agent_model Qwen3-30B-A3B-Instruct-2507 \
    --suite_name travel \
    --attack_name important_instructions \
    --defense_name ipiguard \
    --mode under_attack \
    --output_dir logs
```

The four evaluation settings:

| Setting                                   | `--mode`       | `--defense_name` |
|-------------------------------------------|----------------|------------------|
| Important Instr. attack + IPIGuard        | `under_attack` | `ipiguard`       |
| No attack + IPIGuard                      | `benign`       | `ipiguard`       |
| Important Instr. attack + original model  | `under_attack` | `None`           |
| No attack + original model                | `benign`       | `None`           |

- `--suite_name`: `travel` / `workspace` / `slack` / `banking` / `all`.
- Runs the **full** task set and **resumes** (skips already-logged tasks); add `--force_rerun` to redo, or
  `--uid`/`--iid` to debug a single task/injection.
- Hosted models: pass the id directly, e.g. `--agent_model gpt-4o-mini-2024-07-18`.
- `eval.sh` wraps a single config — edit the vars at the top and `bash eval.sh`.

**Outputs.** AgentDojo layout, one JSON per task:
`logs/{agent_model}[+{defense}]/{suite}/{user_task}/{attack_type}/{injection}.json`. Each file holds the
message trace, `utility`/`security`, and (for IPIGuard) the DAG details
(`initial_dag`, `expanded_dag`, `dag_events`, `new_tool_calls`). Runs print per-suite and overall
**ASR** (↓) and **Utility** (↑).


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
