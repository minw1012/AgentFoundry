# AgentFoundry: Agent Runtime with Contracts, Verifier, and Skill Distillation

This repository contains the runtime implementation of a multi-agent terminal system built around a canonical tool-calling loop.

TLDR: the model decides when to call tools and when to stop; the runtime executes tool calls, enforces policy, records observations, and loops until completion.

## Abstract
Modern agent systems often fail because control logic is overfit to brittle intent routing, or because tool execution lacks robust safety and recovery semantics. This project implements a model-driven runtime where the language model is the controller and the harness is the executor. The harness integrates typed tools, stateful memory, execution traces, and permission-aware policy checks. The system supports document analysis, tabular workflows, local knowledge lookup, code-oriented actions, and optional network/database/browser utilities within explicit trust boundaries. A deterministic fallback path is included for environments where model-native tool control is unavailable.

## Summary Figure

![Publication-style summary figure](dynamic_controller_loop.svg)

The model is responsible for control decisions.
The runtime is responsible for execution, safety checks, and state updates.
When `Need tool call now?` is `No`, the controller can either finish (`FINAL`) or return a clarification question (`CLARIFY/CHAT`) if information is still missing.

## System

### Harness Definition

```text
Harness = Tools + Knowledge + Observation + Action Interfaces + Permissions
```

### Runtime Components
- `DynamicLoopOrchestrator`: primary controller with model-native tool loop and fallback execution path.
- `Constraint/Verifier/Selector pipeline`:
  - `constraint_agent` builds per-step contracts (preconditions/postconditions).
  - `selector_agent` dynamically chooses reasoning/tool/code/clarification actions.
  - `verifier_agent` validates each step output and emits fix suggestions.
- `ToolRegistry`: typed tool catalog with schemas, permissions, ownership, retries, and timeouts.
- `ExecutionPolicy`: risk-aware gating, approval checks, trust boundaries for network/filesystem actions.
- `MemoryStore`: session history, workflow events, knowledge documents, and experience records.
- `ExperienceAgent`: captures solved runs and distills reusable local skills under `skills/distilled/`.
- `terminal_chat.py`: interactive terminal interface for human-in-the-loop execution.

### Main Code Locations
- Runtime and tools: `multi_agent_system.py`
- Terminal interface: `terminal_chat.py`
- Modular entrypoints (phase 1): `src/core`, `src/tools`, `src/agents`, `src/policy`, `src/skills`
- Architecture docs: `docs/architecture.md`, `docs/tools.md`, `docs/dev-guide.md`

## Main Features

### Advanced Agent Capabilities
- Dynamic tool loop with structured action modes (`REASON/TOOL/CODE/CLARIFY/FINAL`) and step-wise verification.
- Contract-guided execution with explicit precondition/postcondition checks before/after each tool call.
- Failure-aware recovery with taxonomy-driven handling (`missing_input`, `parse_error`, `timeout`, `policy_block`, `command_missing`, `json_error`) and automatic replan/clarify paths.
- Experience reflection and skill distillation: successful traces are summarized, quality-gated, deduplicated, and converted into reusable local skills.
- Multimodal workspace understanding for documents, images (including SVG with embedded raster), and videos (frame sampling + vision summary).

### Complex Tooling (Selected)
- Knowledge and retrieval pipeline:
  - `knowledge_ingest_workspace_docs` + `kb_search` + `knowledge_get_doc` + `knowledge_list_sources`
  - Purpose: build and query an in-workspace knowledge base instead of one-shot file reads.
- Tabular analysis and computation pipeline:
  - `read_spreadsheet_preview` + `profile_tabular_columns` + `analyze_tabular_with_python`
  - Purpose: inspect schema/statistics and run ad-hoc pandas analysis inside the runtime boundary.
- ML workflow pipeline (data-gated):
  - `process_data` + `feature_plan` + `model_suggest` + `tune_models` + `train_models` + `evaluate_models` + `error_analyze` + `generate_report`
  - Purpose: run an end-to-end ML path with explicit data path/target checks and report generation.
- Code and execution pipeline:
  - `read_code_file` + `read_code_span` + `replace_text_in_file` + `run_shell_command`
  - Purpose: inspect/edit/run code as first-class agent actions with policy controls.
- Browser-style interaction tools:
  - `browser_open_page` + `browser_click_link` + `browser_find_text` + `browser_get_state`
  - Purpose: support page-level navigation/state extraction when tasks require web-like traversal.
- Multimodal file interpretation:
  - `describe_image_file` for visual explanation of `.svg/.png/.jpg/...`
  - `describe_video_file` for `.mp4/.mov/...` using sampled frames and media metadata.

## Code

### Setup

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Optional (recommended for model-native tool loop):

```bash
export OPENAI_API_KEY="<your_api_key>"
```

Without `OPENAI_API_KEY`, the system runs in deterministic/local fallback mode.

## How to Run

### 1) Start interactive terminal

```bash
python3 terminal_chat.py --workspace . --model gpt-4o
```

`--workspace .` scopes default file and tool operations to the current directory.

### 1b) Start web chatbot (no terminal needed)

```bash
python3 web_chat.py --workspace . --model gpt-4o --host 127.0.0.1 --port 7860 --open
```

Then open `http://127.0.0.1:7860` in browser if `--open` is not used.
The web app uses the same `MultiAgentSystem` runtime and tool execution flow.

### 2) Use built-in commands
- `/help`
- `/tools`
- `/skills list`
- `/skills install <repo_url> [alias] [ref]`
- `/file summarize <path_to_docx_or_pdf>`
- `/raw on|off`
- `/exit`

### 3) Example prompts
- `could you walk through this workspace?`
- `please summarize README.md`
- `analyze data/logreg_dataset.csv`
- `do you find this key d5bbc8180dba11ecb1e81171463288e9 in the json file`
- `could you help me download a data we can run it for logistic regression model?`

### 4) GAIA benchmark quick start

```bash
python3 benchmarks/gaia_runner.py \
  --workspace . \
  --dataset benchmarks/gaia_sample.jsonl \
  --score-mode relaxed \
  --output reports/gaia_benchmark_result.json
```

- Dataset supports JSON or JSONL.
- Question keys: `question` / `prompt` / `task` / `input`.
- Answer keys: `answer` / `gold` / `target` / `final_answer` / `ground_truth`.
- Score modes: `exact`, `contains`, `relaxed`.

Run full dataset with checkpointing and resume (local file):

```bash
python3 benchmarks/gaia_runner.py \
  --workspace . \
  --dataset /absolute/path/to/gaia.jsonl \
  --score-mode relaxed \
  --save-every 10 \
  --resume \
  --output reports/gaia_full_result.json
```

Run by shard (example: split 1-3000 into three jobs):

```bash
python3 benchmarks/gaia_runner.py --workspace . --dataset /absolute/path/to/gaia.jsonl --start-index 1 --end-index 1000 --output reports/gaia_shard_1.json
python3 benchmarks/gaia_runner.py --workspace . --dataset /absolute/path/to/gaia.jsonl --start-index 1001 --end-index 2000 --output reports/gaia_shard_2.json
python3 benchmarks/gaia_runner.py --workspace . --dataset /absolute/path/to/gaia.jsonl --start-index 2001 --end-index 3000 --output reports/gaia_shard_3.json
```

Run directly from Hugging Face:

```bash
python3 benchmarks/gaia_runner.py \
  --workspace . \
  --dataset hf://gaia-benchmark/GAIA \
  --hf-split validation \
  --resume \
  --output reports/gaia_hf_result.json
```

Optional:
- `--hf-config <name>` when the dataset has multiple configs.
- `--hf-cache-dir <path>` to control HF cache location.

## Reliability and Safety

### Failure Recovery
The runtime includes explicit recovery mechanisms:
- failure classification (`missing_input`, `parse_error`, `timeout`, `policy_block`, `command_missing`, `json_error`)
- recovery step synthesis and dynamic insertion
- structured reflection logging (`reason`, `root_cause`, `decision_quality`, `fix_applied`, `outcome`)
- repeat-guard behavior for repetitive failing calls
- focused clarification when recovery budget is exhausted
- step-level contract precheck and post-execution verification (`precondition -> execute -> verify -> recover/replan`)
- verifier notes attached to execution output for traceability

### Experience Distillation
- each completed run can be summarized into an experience entry (`skills/experience_catalog.json`)
- distilled skill generation is gated by quality checks (intent/status/tool-depth/failure-rate)
- distillation is deduplicated against existing skill tool-chains and prior experience signatures
- experience is distilled into a local skill only when gate checks pass (`skills/distilled/<skill_name>/SKILL.md`)
- distilled skills are auto-registered in `skills/skills_manifest.json` with `repo_url=local_distilled`
- distillation decision metadata is persisted on experience entries (`distill_decision`)

### Policy Model
- permission-level risk mapping (`low`, `medium`, `high`)
- explicit approval requirement for high-risk actions
- trusted domain checks for network access
- filesystem boundary checks for database paths

## Reproducibility Notes
- Python package requirements are listed in `requirements.txt`.
- Runtime behavior is deterministic in fallback mode and model-dependent in LLM mode.
- Tool results, observations, and event phases are stored in workflow state for traceability.
