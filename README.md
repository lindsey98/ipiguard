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

Evaluations are launched with `main.py`. The model is a positional argument; `--run-attack` turns the
adversarial run on (omit it for the benign, no-attack run). Results always go under `logs/`.

```bash
# Under attack (IPIGuard defense):
python3 main.py Qwen3.6-35B-A3B --run-attack \
    --attack important_instructions \
    --suites banking slack travel workspace \
    --defense ipiguard

# No attack (benign) — same, minus --run-attack/--attack:
python3 main.py Qwen3.6-35B-A3B \
    --suites banking slack travel workspace \
    --defense ipiguard
```

- **MODEL** (positional): hosted (`claude-sonnet-4-5-20250929`, `gpt-4o-mini-2024-07-18`) or local via an
  OpenAI-compatible server (`Qwen3.6-35B-A3B`, or `local:Qwen3.6-35B-A3B`; set `LOCAL_BASE_URL`, see
  [API Keys](#-api-keys)).
- `--defense None` runs the **original model** with no defense; `--defense ipiguard` runs the proposed
  defense.
- `--suites` takes any AgentDojo suite (`banking slack travel workspace`) and/or AgentDyn suite
  (`shopping github dailylife`), or a group: `all` (AgentDojo 4), `agentdyn` (3), `everything` (all 7).

### Using the shell script

`eval.sh` wraps a single configuration (fixed `logs/` output, so interrupted runs resume — completed
trace JSONs are skipped). Edit the variables at the top and run `bash eval.sh`.

### Argument reference

| Argument          | Description                                                                                       |
|-------------------|---------------------------------------------------------------------------------------------------|
| `MODEL` (positional) | Agent model, e.g. `claude-sonnet-4-5-20250929`, `gpt-4o-mini-2024-07-18`, `Qwen3.6-35B-A3B`, `local:Qwen3.6-35B-A3B`. |
| `--run-attack`    | Run under attack. Omit for the benign (no-attack) run.                                              |
| `--attack`        | Adversarial attack to simulate (only with `--run-attack`). `important_instructions` (default), or [ChatInject](https://github.com/hwanchang00/ChatInject): `chat_inject_qwen3` / `chat_inject_glm` (single-turn) and their `_with_utility_system_multiturn_7` / `_with_utility_authority_endorsement_system_multiturn_7` variants. |
| `--defense`       | `ipiguard` for the proposed defense, or `None` for the original (undefended) model.                |
| `--suites`        | Space-separated suites: `banking slack travel workspace` (AgentDojo); `shopping github dailylife` (AgentDyn); or a group: `all`, `agentdyn`, `everything`. |
| `--benchmark-version` | Suite version (default `v1.2`). The AgentDyn suites are unversioned and available under every version. |
| `--output_dir`    | Output directory (default `logs/`). JSON logs + per-suite ASR/Utility.                              |
| `-ut` / `--user-task` | Debug: run only the given user-task id(s), repeatable (`-ut 0 -ut 3`).                          |
| `-it` / `--injection-task` | Debug: run only the given injection-task id(s), repeatable (`-it 1`).                      |
| `--force_rerun`   | Rerun tasks even when a completed trace JSON already exists in `output_dir` (by default completed tasks are skipped and their recorded results reused). |
| `--html`          | Also write a rendered `<task>.html` next to each `<task>.json` trace (pre-plan, committed DAG, runtime tool-call gating, message stream). Off by default. |

Each run prints and saves **ASR** (Attack Success Rate ↓, lower is better) and **Utility** (task success ↑,
higher is better) per suite and overall.
