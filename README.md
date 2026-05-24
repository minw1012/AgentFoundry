# Multiagents: A Model-Driven Tool-Using Agent Runtime

This repository contains the runtime implementation of a multi-agent terminal system built around the canonical tool-calling loop.

TLDR: The model decides when to call tools and when to stop; the runtime executes tool calls, enforces policy, records observations, and loops until completion.

### Abstract
Modern agent systems often fail because control logic is hard-coded around brittle intent routing, or because tool execution lacks robust safety and recovery semantics. This repository implements a model-driven runtime that treats the language model as the controller and the harness as the executor. The harness integrates structured tools, stateful memory, observation logs, and permission-aware policy checks. The system supports knowledge retrieval, document summarization, tabular analysis, code-oriented actions, and optional network/database/browser utilities under explicit trust boundaries. A fallback planner-executor path is provided for degraded environments where model-native tool control is unavailable.

### Core Agent Pattern

```text
                    THE AGENT PATTERN
                    =================

    User --> messages[] --> LLM --> response
                                      |
                            stop_reason == "tool_use"?
                           /                          \
                         yes                           no
                          |                             |
                    execute tools                    return text
                    append results
                    loop back -----------------> messages[]
```

The model decides when to call tools and when to stop.
The runtime executes exactly what the model requests, subject to policy constraints.

## System

### Harness Definition

```text
Harness = Tools + Knowledge + Observation + Action Interfaces + Permissions
```

### Runtime Components
- `DynamicLoopOrchestrator`: primary controller with model-native tool loop and fallback execution path.
- `ToolRegistry`: typed tool catalog with schemas, ownership, permissions, retries, and timeouts.
- `ExecutionPolicy`: risk-aware gating, approval checks, trust boundaries for network and filesystem access.
- `MemoryStore`: session history, workflow events, knowledge documents, and reusable experience records.
- `terminal_chat.py`: interactive terminal interface for human-in-the-loop operation.

### Main Code Locations
- Runtime and tools: `multi_agent_system.py`
- Terminal interface: `terminal_chat.py`
- Design notes: `system_redesign.md`
- Communication notes: `multi_agent_commu.md`

## Capabilities

### Task Families
- Knowledge lookup from local workspace content and ingested references.
- Document reading and summarization for `.pdf`, `.docx`, `.txt`, `.md`.
- Tabular analysis for `.csv` and `.xlsx`.
- ML workflow blocks: preprocessing, model suggestion, tuning, training, evaluation, reporting.
- Code-task actions: read/search/edit files and run shell commands.
- Optional utilities: network HTTP calls, sqlite queries, browser-like page inspection.

### Representative Tools
- File and search: `list_workspace_files`, `search_workspace_text`, `read_text_file`, `write_text_file`
- Document: `read_document_file`, `summarize_text`, `extract_key_points`
- Tabular: `read_spreadsheet_preview`, `profile_tabular_columns`, `analyze_tabular_with_python`
- Code: `read_code_file`, `read_code_span`, `replace_text_in_file`, `run_shell_command`
- ML: `process_data`, `model_suggest`, `tune_models`, `train_models`, `evaluate_models`, `generate_report`
- Knowledge: `kb_search`, `knowledge_ingest_workspace_docs`, `knowledge_list_sources`, `knowledge_get_doc`
- Skills: `skill_install_from_git`, `skill_list_installed`

## Code

### Setup

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Optional: enable model-native tool loop with OpenAI Responses API.

```bash
export OPENAI_API_KEY="<your_api_key>"
```

Without `OPENAI_API_KEY`, the system runs in deterministic/local fallback mode.

### Interactive Run

```bash
python3 terminal_chat.py --workspace .
```

`--workspace .` scopes default file and tool operations to the current directory.

### Useful Terminal Commands
- `/help`
- `/tools`
- `/skills list`
- `/skills install <repo_url> [alias] [ref]`
- `/file summarize <path_to_docx_or_pdf>`
- `/raw on|off`
- `/exit`

### Example Prompts
- `could you walk through this workspace?`
- `please summarize README.md`
- `analyze data/logreg_dataset.csv`
- `do you find this key d5bbc8180dba11ecb1e81171463288e9 in the json file`
- `could you help me download a data we can run it for logistic regression model?`

## Reliability and Safety

### Failure Recovery
The runtime includes explicit recovery mechanisms:
- failure classification (`missing_input`, `parse_error`, `timeout`, `policy_block`, `command_missing`, `json_error`)
- recovery step synthesis and dynamic insertion
- reflection logging and repeat-guard behavior
- focused clarification when recovery budget is exhausted

### Policy Model
- Permission-level risk mapping (`low`, `medium`, `high`)
- Approval requirement for high-risk actions
- Trusted domain checks for network access
- Filesystem boundary checks for database paths

## Reproducibility Notes
- Python package requirements are minimal and listed in `requirements.txt`.
- Runtime behavior is deterministic in fallback mode and model-dependent in LLM mode.
- Tool results, observations, and event phases are stored in workflow state for traceability.

## Limitations
- This project is a runtime harness, not a benchmark-trained autonomous model.
- End quality depends on available tools, data accessibility, and model quality.
- Some advanced domains are scaffoldable but not fully productized end-to-end pipelines.
