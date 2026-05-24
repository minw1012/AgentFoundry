# Multiagents

A Codex-inspired, model-driven agent runtime for terminal workflows.

It is built around one core idea:
- the model decides when to call tools
- the runtime executes tool calls and feeds results back
- the loop continues until the model stops

## The Agent Pattern

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


    The model decides when to call tools and when to stop.
    The code just executes what the model asks for.
    This repo builds everything around this loop.
```

## Harness Design

```text
Harness = Tools + Knowledge + Observation + Action Interfaces + Permissions
```

- `Tools`: file I/O, shell, document parsing, tabular analysis, network, sqlite, browser-like inspection
- `Knowledge`: local markdown/docs + ingested references + searchable memory
- `Observation`: tool outputs, workflow events, git/log/browser state tools
- `Action Interfaces`: CLI chat, structured tool calls, code/file updates, command execution
- `Permissions`: policy-based risk checks (low/medium/high), trust boundaries, explicit approval for risky actions

## Runtime Behavior

`DynamicLoopOrchestrator` (`multi_agent_system.py`) runs in this order:

1. Try model-native tool loop first (OpenAI Responses + tools).
2. If unavailable, use local fallback planning and execution.
3. Execute tools, store observations, reflect/recover when needed.
4. Return final answer or focused clarification.

## What This Project Can Do

- Knowledge lookup from workspace docs/history
- Document summary (`.pdf/.docx/.txt/.md`)
- Tabular data analysis (`.csv/.xlsx`)
- ML workflow blocks (prep, model suggest, train, evaluate, report)
- Code-task support (read/edit/search/run command)
- Skill install/list from Git repositories
- Network/sqlite/browser-style utility calls (policy controlled)

## Quick Start

### 1) Install dependencies

```bash
python3 -m pip install -r requirements.txt
```

### 2) (Optional) enable model-driven tool loop

```bash
export OPENAI_API_KEY="your_key"
```

Without API key, the system still runs with local fallback logic.

### 3) Start terminal chat

```bash
python3 terminal_chat.py --workspace .
```

`--workspace .` means tool execution and file operations are scoped to the current directory.

## Terminal Commands

- `/help`
- `/tools`
- `/skills list`
- `/skills install <repo_url> [alias] [ref]`
- `/file summarize <path_to_docx_or_pdf>`
- `/raw on|off`
- `/exit`

## Representative Tool Groups

- File + search: `list_workspace_files`, `search_workspace_text`, `read_text_file`, `write_text_file`
- Document: `read_document_file`, `summarize_text`, `extract_key_points`
- Tabular: `read_spreadsheet_preview`, `profile_tabular_columns`, `analyze_tabular_with_python`
- Code: `read_code_file`, `read_code_span`, `replace_text_in_file`, `run_shell_command`
- ML: `process_data`, `model_suggest`, `train_models`, `evaluate_models`, `generate_report`
- Knowledge: `kb_search`, `knowledge_ingest_workspace_docs`, `knowledge_list_sources`
- Skills: `skill_install_from_git`, `skill_list_installed`
- Network/DB/Browser: `network_http_request`, `sqlite_query`, `browser_open_page`
- Observation: `observe_git_diff`, `observe_error_logs`, `observe_recent_events`

## Example Prompts

- `could you walk through this workspace?`
- `please summarize README.md`
- `analyze data/logreg_dataset.csv`
- `do you find this key d5bbc8180dba11ecb1e81171463288e9 in the json file`
- `could you help me download a data we can run it for logistic regression model?`

## Safety Notes

- High-risk actions are policy-gated and may require explicit approval.
- Network and database calls are constrained by trust-boundary checks.
- The agent prefers clarification over repeating failing actions.

## File Map

- Main runtime: `multi_agent_system.py`
- Terminal UI: `terminal_chat.py`
- Design notes: `system_redesign.md`
- Loop reference: `multi_agent_commu.md`
