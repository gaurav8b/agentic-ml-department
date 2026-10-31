# LangGraph and LangChain — Practical Walkthrough of This Project

This guide explains exactly what each library is doing here, without assuming prior experience.

## 1. The difference in one sentence

- **LangChain helps the application communicate with a language model.**
- **LangGraph controls the order of work, remembers progress and pauses for human approval.**

The project uses both, but most of its business and ML work is normal Python code.

## 2. Where to look in the source code

| File | What to look for |
|---|---|
| `src/agentic_ml_department/workflow.py` | State definition, graph nodes, approval interrupts, routes and checkpoint storage |
| `src/agentic_ml_department/advisor.py` | Deterministic business questions and optional `ChatOllama` call through LangChain |
| `src/agentic_ml_department/api.py` | How a user starts a workflow and resumes it after approval |
| `dashboard/app.py` | How approvals are shown and sent to the API |
| `src/agentic_ml_department/modeling.py` | The ML work that the workflow delegates to ordinary Python code |

## 3. LangGraph concept 1 — state

State is the shared record of what has happened so far and what later steps need. The project declares `MLDepartmentState` in `workflow.py`.

It keeps values such as:

- `run_id`: identifier for this particular business job.
- `objective`: churn risk or lead conversion.
- `supervisor_instructions`: guidance supplied by the user.
- `business_snapshot`: discovered business systems and profiles.
- `business_question_proposal`: questions suggested for approval.
- `question_approval`: what the supervisor decided.
- `model_result`: training metrics, model file and queued prediction count.
- `model_approval`: model promotion decision.
- `writeback_approval`: permission for the synthetic CRM update.
- `business_impact`: estimate of the possible business value.

A state field is not permission. It is a record. The code checks the approval decision before routing to the next stage.

## 4. LangGraph concept 2 — nodes

A node is one defined unit of work. In this project, `_discover`, `_profile`, `_propose_questions`, `_train`, `_promote_model`, `_sync` and other functions are nodes.

A node receives the current state and returns only the information it adds or changes. For example:

```python
def _profile(state: MLDepartmentState) -> dict:
    snapshot = state.get("business_snapshot", {})
    profiles = snapshot.get("profiles", [])
    compact = [
        {key: profile.get(key) for key in
         ("source", "rows", "columns", "missing_cells", "duplicate_rows")}
        for profile in profiles
    ]
    return {"data_profiles": compact}
```

This node does not need a language model. It summarizes information that deterministic code has already gathered.

## 5. LangGraph concept 3 — edges and conditional routes

Edges say which node should run next. Conditional edges branch based on a returned state value.

The project's question approval route is:

```python
def _route_question(state: MLDepartmentState) -> str:
    return "train" if state.get("question_approval", {}).get("approved") else "stop"
```

The graph then maps the returned string to the next node:

```python
graph.add_conditional_edges(
    "approve_business_question",
    _route_question,
    {"train": "train_candidate_models", "stop": "stop"},
)
```

This is deliberately plain. If the supervisor did not approve, there is no path to the training node.

## 6. LangGraph concept 4 — interrupt (pause for a person)

The approval nodes use LangGraph's `interrupt()` function. It stops the workflow and sends a JSON-style approval request to the caller.

A simplified example:

```python
from langgraph.types import interrupt

def _question_gate(state):
    decision = interrupt({
        "approval_type": "business_question",
        "title": "Approve the business question",
        "proposal": state["business_question_proposal"],
    })
    return {"question_approval": decision}
```

The dashboard displays this request. A human chooses Approve or Reject and can add comments. The decision is sent to the API and the graph resumes.

## 7. LangGraph concept 5 — checkpoint and resume

A checkpoint is the saved state of a workflow. It is similar to saving a document before closing it: the application can come back to the same work later.

This project uses a SQLite checkpointer for its single-process local demonstration:

```python
connection = sqlite3.connect(checkpoint_path, check_same_thread=False)
checkpointer = SqliteSaver(connection)
checkpointer.setup()
graph = builder.compile(checkpointer=checkpointer)
```

Each run has a `thread_id` equal to its `run_id`. When a person approves, the API resumes the same thread:

```python
config = {"configurable": {"thread_id": run_id}}
result = graph.invoke(Command(resume=decision), config=config)
```

This is what allows the user to approve the business question, inspect the model later and then approve writeback without one huge uninterrupted process.

**Production note:** SQLite checkpointing is deliberately limited to a lightweight demonstration. For several API workers or a production service, use a supported durable checkpointer such as PostgreSQL-backed LangGraph checkpoints and test restart/recovery behavior.

## 8. Where LangChain is used

`advisor.py` first creates a small, deterministic set of business questions. If the user turns on Ollama, the adviser also calls a local chat model using LangChain:

```python
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

llm = ChatOllama(
    model=settings.ollama_model,
    base_url=settings.ollama_base_url,
    temperature=0.1,
)
response = llm.invoke([
    SystemMessage(content="You are a cautious business analytics adviser."),
    HumanMessage(content=prompt),
])
```

The system prompt tells the adviser to suggest testable questions and avoid claiming causation. The optional response is displayed for review; it does not run a model, update a CRM or bypass an approval gate.

## 9. Enable the local language model

1. Install Ollama on the host computer.
2. Pull an instruct model that your hardware can run.
3. Set `AGENT_LLM_PROVIDER=ollama` in `.env`.
4. Set `OLLAMA_MODEL` to the exact model name shown by `ollama list`.
5. Confirm `OLLAMA_BASE_URL` points from the container to the host. Docker Desktop typically supports `host.docker.internal`; Linux may require an explicit host-gateway configuration.
6. Rebuild/restart the API service.

Without a local model, the application still works. It uses the deterministic advisor and the same approval flow.

## 10. How to add a new business workflow

For a new department or a new ML objective:

1. Define the business objective and an owner.
2. Define its state fields and permitted tools.
3. Write one deterministic node per auditable stage.
4. Add an approval interrupt before each consequential or policy-sensitive stage.
5. Add conditional routing so rejected work cannot reach later actions.
6. Add an independent reviewer or automated acceptance test.
7. Store the exact outputs and decisions in durable storage.
8. Add tests for both approval and rejection paths.
9. Add monitoring and an explicit rollback path.

Do not expose a tool to an agent simply because an integration library supports it. Every tool must have an owner, narrow permission scope, validated inputs and a defined failure response.

## 11. Further official reading

- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)
- [LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)
- [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- [LangChain overview](https://docs.langchain.com/oss/python/langchain/overview)
- [LangChain Ollama integration](https://python.langchain.com/docs/integrations/chat/ollama/)


## 12. Why this project now has specialist Python agents

A useful reference is [AutoGluon Assistant (MLZero)](https://github.com/gaurav8b/autogluon-assistant), which has distinct Python agents for data perception, task description, tool selection, code generation, execution and error analysis, plus a manager that iterates across candidate solutions. It also provides CLI, Python API, Web UI and MCP interfaces. Its `pyproject.toml` declares both `langgraph` and `langchain`.

We adapt the role separation that fits a supervised business ML department:

- `agents.run_data_perception` inspects the data profiles and flags material missingness.
- `agents.run_task_planner` builds a six-stage business plan, including the three approval points.
- `agents.run_tool_selector` picks only the tools defined in `tool_registry.py`.
- `agents.run_reviewer` checks that there is a holdout evaluation, a historical training cohort, a separate current scoring population, an artifact reference and a passing quality gate.
- `workflow.py` records the agent trace so a user can see what each specialist did.

The system deliberately does **not** implement a free-form code-generation/execution loop. MLZero documents Python and Bash generation/execution and recommends Docker isolation. For this prototype, generated code would make a business connector too powerful and would make it harder to verify exactly what action an agent can take. The ML operations therefore run through known Python functions and scikit-learn pipelines.

## 13. Inspect the team and run from Python

The team and its registered tools are visible at `GET /api/agent-team`. The Streamlit dashboard shows the task plan, selected tool list, model review and per-run agent trace.

Command-line usage:

```bash
agentic-ml profile
agentic-ml run --objective customer_churn --instructions "Prioritize recall"
```

Python usage (from an installed project environment):

```python
from agentic_ml_department.agents import run_data_perception, run_task_planner
from agentic_ml_department.connectors import business_system_summary

profiles = business_system_summary()["profiles"]
perception = run_data_perception(profiles)
plan = run_task_planner("customer_churn", perception["profiles"], "Prioritize recall")
print(plan["plan"])
```

The tool registry validates required and unexpected arguments, rejects unknown tool names and prevents a write-capable tool from running unless explicit approval is supplied. The registry is a first capability-control layer; a production deployment must also enforce identity, permissions and network/data scopes at the service boundary.
