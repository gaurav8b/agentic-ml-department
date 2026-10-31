# How this project relates to AutoGluon Assistant (MLZero)

## What MLZero provides

[AutoGluon Assistant](https://github.com/gaurav8b/autogluon-assistant), also called MLZero, is a research-oriented multi-agent system for automating end-to-end machine-learning work. Its repository README identifies it as the official implementation of the MLZero paper and documents CLI, Python API, Web UI and MCP interfaces. Its `pyproject.toml` declares `langgraph`, `langchain`, and several LangChain provider packages.

Its Python source includes specialist agents for data perception, task description, tool selection, code generation, code execution, error analysis, retrieval and chat. The coding agent delegates to a node manager which explores candidate solutions through an iterative search process. This is much more than a collection of scripts: the Python modules implement the actual agent behavior and orchestration.

MLZero is research code, not a drop-in production business department. Its README explicitly warns that it executes language-model-generated code and recommends container isolation. The repository also carries significant ML ecosystem dependencies and should be evaluated for the environment and problem type before adoption.

## What we borrow

This project adopts the reusable design patterns that fit a business-supervised ML department:

| MLZero pattern | Our implementation | Why it is useful |
|---|---|---|
| Data-perception agent | `agents.run_data_perception` | Makes dataset understanding an explicit first-class step |
| Task-descriptor agent | `agents.run_task_planner` | Turns a business objective into a visible plan |
| Tool-selector agent | `agents.run_tool_selector` | Separates tool choice from tool execution |
| Specialist agents | Typed Python modules with structured outputs | Makes responsibilities testable and easier to explain |
| Manager / orchestration | LangGraph workflow | Keeps order, state, decisions, pause/resume and checkpoints explicit |
| Iterative improvement | Verified outcomes, business review records and future approved training runs | Uses observed outcomes rather than simply trusting a model's self-evaluation |
| CLI / Python / Web interfaces | CLI, Python package, FastAPI and Streamlit | Serves both technical operators and business supervisors |

## What we deliberately do not copy

The demo does not execute arbitrary Python or Bash code written by a language model. A business automation agent that can generate and execute code with broad access could read unrelated data, expose credentials, corrupt data or change business records. Instead, agents select from a small, explicit Python tool registry. Each tool has declared inputs, a risk level and an approval requirement. Unknown tools and unexpected inputs are rejected. A write-capable tool cannot run without an explicit approval signal, and the LangGraph workflow separately pauses at the business-system writeback gate.

We also do not copy MLZero's full search strategy, multimodal AutoGluon training stack, retriever/reranker ecosystem or GPU-heavy dependencies simply because they exist. They may be valuable later for specific data types and use cases, but they are not necessary for the tabular customer-churn and lead-conversion prototype. The initial aim is a small, reproducible, understandable business workflow.

## Where to explore in this repository

- `src/agentic_ml_department/agents/` — the specialist agent layer.
- `src/agentic_ml_department/tool_registry.py` — allow-listed tool capabilities and guardrails.
- `src/agentic_ml_department/workflow.py` — LangGraph state and approval lifecycle.
- `src/agentic_ml_department/modeling.py` — deterministic scikit-learn training and scoring.
- `src/agentic_ml_department/cli.py` — command-line interface.
- `dashboard/app.py` — business-supervisor user interface.
- `tests/test_business_ml.py` — model and new agent/tool-boundary tests.

## Practical conclusion

MLZero is a valuable reference for agent decomposition, data perception, tool selection, iterative development and multiple user interfaces. This project adapts those patterns to a narrower goal: a supervised business ML department that can connect to company data, propose questions, train and evaluate approved models, prepare business actions, request human approvals and learn from verified outcomes. The two projects have different goals and risk postures; this repository should borrow ideas rather than reproduce the entire research framework.
