<h2 align="center">
  <strong>IPIGuard</strong>: A Novel Tool Dependency Graph-Based Defense Against Indirect Prompt Injection in LLM Agents
</h2>

<!-- <p align="center">
  <a href="https://greysahy.github.io/" target="_blank">Hengyu An</a><sup>1</sup> &nbsp; | &nbsp;
  <a href="https://jzhang538.github.io/jinghuaizhang/" target="_blank">Jinghuai Zhang</a><sup>2</sup> &nbsp; | &nbsp;
  <a href="https://tydusky.github.io/" target="_blank">Tianyu Du</a><sup>1</sup> &nbsp; | &nbsp;
  Chunyi Zhou<sup>1</sup> &nbsp; | &nbsp;
  Qingming Li<sup>1</sup> &nbsp; | &nbsp;
  <a href="https://tlin-taolin.github.io/" target="_blank">Tao Lin</a><sup>3</sup> &nbsp; | &nbsp;
  <a href="https://nesa.zju.edu.cn/index.html/" target="_blank">Shouling Ji</a><sup>1</sup>
</p>

<p align="center" style="font-size: 1rem;">
  <sup>1</sup> Zhejiang University &nbsp;&nbsp;
  <sup>2</sup> University of California, Los Angeles &nbsp;&nbsp;
  <sup>3</sup> Westlake University
</p> -->

<br>
<br>


<!-- <p align="center">
<a href="https://huggingface.co/sp12138sp/UCGM">:robot: Models</a> &ensp;
<a href="https://arxiv.org/abs/2505.07447">:page_facing_up: Paper</a> &ensp;
<a href="#label-bibliography">:label: BibTeX</a> &ensp;
  <br><br>
<a href="https://paperswithcode.com/sota/image-generation-on-imagenet-256x256?p=unified-continuous-generative-models"><img src="https://img.shields.io/endpoint.svg?url=https://paperswithcode.com/badge/unified-continuous-generative-models/image-generation-on-imagenet-256x256" alt="PWC"></a> <a href="https://paperswithcode.com/sota/image-generation-on-imagenet-512x512?p=unified-continuous-generative-models"><img src="https://img.shields.io/endpoint.svg?url=https://paperswithcode.com/badge/unified-continuous-generative-models/image-generation-on-imagenet-512x512" alt="PWC"></a>
</p> -->

<div align='center'>
  <img src="assets/figure.png" width="75%">
  <p>
    <strong>Comparison of the traditional task execution paradigm (top) and our IPIGUARD (bottom)</strong>
  </p>
</div>

## 📢 News

- [2025.09.15] **IPIGuard** is selected for **Oral presentation** at EMNLP 2025
- [2025.08.21]🎉 Our paper **"IPIGuard: A Novel Tool Dependency Graph-Based Defense Against Indirect Prompt Injection in LLM Agents"** has been **accepted to EMNLP 2025 Main Conference**!


## 📖 Overview

IPIGuard evaluates LLM agents against **indirect prompt injection (IPI)** attacks on top of the
[AgentDojo](https://github.com/ethz-spylab/agentdojo) benchmark (v0.1.35), extended with the three
dynamic suites from [AgentDyn](https://github.com/SaFo-Lab/AgentDyn) (`shopping`, `github`,
`dailylife` — 60 open-ended user tasks and 560 injection test cases). Every evaluation is defined by
three choices:

- **Agent model** — the LLM that drives the agent. Hosted (e.g. `claude-sonnet-4-5-20250929`,
  `gpt-4o-mini-2024-07-18`) or local via an OpenAI-compatible server (e.g. `Llama-3.3-70B-Instruct`).
- **Attack** — the adversarial content injected into tool outputs (e.g. `important_instructions`), only
  active in `under_attack` mode.
- **Defense** — the defense strategy applied to the agent. Use `ipiguard` for the proposed defense, or
  `None` to run the **original model** with no defense.

This README walks through the four combinations of *(attack on / off)* × *(IPIGuard / original model)* using
Anthropic's **`claude-sonnet-4-5-20250929`** as the agent model.


## 🔧 Installation

We recommend using Python ≥3.10.

```bash
# git clone
git clone https://github.com/lindsey98/ipiguard.git
cd ipiguard

# create conda environment
conda create -n ipiguard python=3.10
conda activate ipiguard

# install the bundled agentdojo (editable). This vendored copy is based on
# agentdojo 0.1.35 and already includes the AgentDyn suites (shopping, github,
# dailylife) — no separate AgentDyn installation is needed.
cd agentdojo
pip install -e .
cd ..
```

> Upgrading from an older checkout? Re-run `pip install -e .` inside `agentdojo/` — the
> 0.1.35 base adds dependencies such as `google-genai` and `deepdiff`.


## 🔑 Setup API Keys

Rename `.env.example` to `.env` and populate it with your API keys
   (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`).
Load the keys into your environment before running:
```bash
set -a && source .env && set +a
```


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

All examples below use the agent model **`anthropic:claude-sonnet-4-5-20250929`** and the `travel` suite.
Swap `--suite_name` for any AgentDojo suite (`workspace`, `slack`, `banking`, `travel`) or AgentDyn
suite (`shopping`, `github`, `dailylife`), or use a group: `all` (the four AgentDojo suites),
`agentdyn` (the three AgentDyn suites), or `everything` (all seven). To run on a local model
instead, set `LOCAL_BASE_URL` (see [API Keys](#-api-keys)) and replace
`--agent_model claude-sonnet-4-5-20250929` with `--agent_model Qwen3.6-35B-A3B`.

### 1) Important Instr. attack + IPIGuard defense

```bash
python3 run/eval.py \
    --suite_name travel \
    --agent_model Llama-3.3-70B-Instruct \
    --attack_name important_instructions \
    --defense_name ipiguard \
    --mode under_attack \
    --output_dir logs/ \
```

### 2) No attack + IPIGuard defense

```bash
python3 run/eval.py \
    --suite_name travel \
    --agent_model claude-sonnet-4-5-20250929 \
    --attack_name important_instructions \
    --defense_name ipiguard \
    --mode benign \
    --output_dir logs/ \
```

### 3) Important Instr. attack + original model (no defense)

```bash
python3 run/eval.py \
    --suite_name travel \
    --agent_model claude-sonnet-4-5-20250929 \
    --attack_name important_instructions \
    --defense_name None \
    --mode under_attack \
    --output_dir evaluation_results/attack_original \
    --uid 0 --iid 0
```

### 4) No attack + original model (no defense)

```bash
python3 run/eval.py \
    --suite_name travel \
    --agent_model claude-sonnet-4-5-20250929 \
    --attack_name important_instructions \
    --defense_name None \
    --mode benign \
    --output_dir evaluation_results/benign_original \
    --uid 0 --iid 0
```

### Using the shell script

`eval.sh` wraps a single configuration with a fixed `logs/` output dir, so interrupted runs resume
where they left off (completed trace JSONs are skipped). Edit the variables at the top and run it:

```bash
# inside eval.sh
agent_model="local:Qwen3.6-35B-A3B"
attack_name="important_instructions"
defense_name="ipiguard"          # or "None" for the original model
suite_name="all"                 # or "agentdyn" / "everything" / a single suite
mode="under_attack"              # or "benign"
```

```bash
bash eval.sh
```

### Argument reference

| Argument          | Description                                                                                       |
|-------------------|---------------------------------------------------------------------------------------------------|
| `--agent_model`   | Agent model used for evaluation (e.g. `claude-sonnet-4-5-20250929`, `gpt-4o-mini-2024-07-18`, `Llama-3.3-70B-Instruct`). |
| `--attack_name`   | Adversarial attack to simulate. `important_instructions` (default); [ChatInject](https://github.com/hwanchang00/ChatInject) chat-template attacks: `chat_inject_qwen3` / `chat_inject_glm` (single-turn) and their `_with_utility_system_multiturn_7` / `_with_utility_authority_endorsement_system_multiturn_7` variants; or [ASB](https://github.com/agiresearch/ASB) observation prompt injection: `asb_opi_naive`, `asb_opi_fake_completion`, `asb_opi_escape_characters`, `asb_opi_context_ignoring`, `asb_opi_combined_attack`. Ignored in `benign` mode. |
| `--defense_name`  | Defense strategy: `ipiguard` for the proposed defense, or `None` for the original (undefended) model. |
| `--suite_name`    | Task suite/domain: `travel`, `workspace`, `slack`, `banking` (AgentDojo); `shopping`, `github`, `dailylife` (AgentDyn); or a group: `all` (AgentDojo), `agentdyn`, `everything`. |
| `--benchmark_version` | Suite version (default `v1.2`). The AgentDyn suites are unversioned and available under every version. |
| `--mode`          | `benign` → standard tasks without attacks; `under_attack` → adversarial tasks with injected attacks. |
| `--output_dir`    | Directory to store evaluation results (JSON logs + per-suite ASR/Utility).                          |
| `--uid` / `--iid` | Debug filters: run only the given user-task / injection-task ID.                                    |
| `--force_rerun`   | Rerun tasks even when a completed trace JSON already exists in `output_dir` (by default completed tasks are skipped and their recorded results reused). |

Each run prints and saves **ASR** (Attack Success Rate ↓, lower is better) and **Utility** (task success ↑,
higher is better) per suite and overall.
