# Technology Choices — Open-Source, Self-Hosted and Practical

This is a proof-of-concept stack, not a claim that one framework is best for every enterprise. The selection prioritizes open-source components, a local-first demonstration, readable code, explicit human approval and the ability to replace individual components later.

## 1. Selected stack

| Layer | Selected tool | Why it is used | Main role in this repository |
|---|---|---|---|
| Workflow orchestration | LangGraph | Explicit state, branching, pause/resume and persistent checkpoints | Owns the controlled sequence and approval gates |
| LLM and tool integration | LangChain | Model/provider abstractions and integration components | Optional natural-language business-question advice |
| Local language model runtime | Ollama | Can run compatible models on the user's own computer | Optional local adviser, no required paid API |
| Database | PostgreSQL | Mature relational database with transactions and broad ecosystem support | Stores synthetic CRM, leads, orders, campaigns, support and audit/workflow data |
| Data access | SQLAlchemy | Widely used Python database toolkit with multiple database dialects | Maps business tables into Python code |
| Data processing | pandas and NumPy | Practical tabular data handling and repeatable synthetic data generation | Profiles datasets and builds training tables |
| Machine learning | scikit-learn | Strong, well-documented baseline ML with preprocessing pipelines and evaluation tools | Logistic regression, random forest, metrics and feature preparation |
| Experiment tracking | MLflow | Self-hostable experiment tracking and artifact history | Saves run metadata, metrics and model artifacts |
| API | FastAPI | Type-annotated Python APIs and generated OpenAPI documentation | Department control plane and synthetic business-system APIs |
| User interface | Streamlit | Fast route to a usable Python dashboard | Business-user approval and monitoring console |
| Packaging | Docker Compose | Reproducible multi-service local environment | Starts PostgreSQL, MLflow, API and dashboard together |

## 2. Why LangGraph is the orchestration choice

The main challenge here is not “make a chatbot answer a question.” It is “run a workflow that may last several stages, pause while a person reviews something, preserve its state and continue only after a recorded decision.”

LangGraph is designed for stateful, long-running workflows and supports persistent checkpoints and interrupts. That makes it a good fit for approval gates and supervised execution. A normal sequential script can run the same steps, but managing state across human waiting time, retries and restarts becomes increasingly difficult.

Official references:

- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)
- [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- [LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)
- [Python reference](https://reference.langchain.com/python/langgraph/overview)

## 3. Why LangChain is present as a separate layer

LangChain is used where a language model adds value: interpreting a business objective, generating optional explanatory questions and working with provider-specific chat integrations. In this prototype the `ChatOllama` integration calls a local Ollama model when enabled.

LangChain does not decide whether a user has permission to promote a model or modify a CRM. Those decisions are controlled by FastAPI validations, LangGraph state and explicit approval payloads.

Official references:

- [LangChain open-source stack](https://www.langchain.com/oss-overview)
- [LangChain agents](https://docs.langchain.com/oss/python/langchain/agents)
- [Ollama API introduction](https://docs.ollama.com/api/introduction)

## 4. Why not use an agent framework for every operation?

An enterprise workflow should not send every task to a free-form agent. Database counts, schema inspection, metric calculation, permission checking and record updates are better as predictable, testable code. An LLM can help interpret an ambiguous question, but fixed controls should remain ordinary application logic.

The code therefore follows a hybrid approach:

- Deterministic code for database access, data validation, model training, metrics, workflow routing, approval checks and writeback.
- Optional LLM assistance for language-based question suggestions.
- Human review for business objectives, model release and integration actions.

## 5. Why scikit-learn and MLflow?

The first problem is tabular classification. Scikit-learn provides a readable way to build a preprocessing pipeline, compare common baselines and calculate metrics. It is more appropriate for an introductory project than beginning with a large custom neural network.

MLflow records experiment parameters, metrics and model artifacts. Its model-registry functionality can be expanded for fuller model lifecycle management; this prototype stores a compact application-level registry alongside MLflow experiment tracking.

Official references:

- [scikit-learn user guide](https://scikit-learn.org/stable/user_guide.html)
- [MLflow Tracking](https://mlflow.org/docs/latest/ml/tracking/)
- [MLflow Model Registry](https://mlflow.org/docs/latest/ml/model-registry/)

## 6. Why PostgreSQL instead of a file-only database?

A local SQLite database is useful for a small test and is used by the automated tests. The main Docker demonstration uses PostgreSQL because it is closer to a shared company database and can handle multiple application connections and concurrent workflows more naturally. The LangGraph checkpointer remains SQLite in this POC because it is a small single-process demonstration; migrate it to a supported PostgreSQL checkpointer before a multi-process production deployment.

## 7. Why not embed AutoGluon Assistant / MLZero directly?

[AutoGluon Assistant (MLZero)](https://github.com/autogluon/autogluon-assistant) is a relevant reference project for end-to-end multi-agent machine-learning automation. It can transform data into ML solutions with limited manual configuration. It is useful to study for ML automation ideas.

This repository takes a narrower approach because the teaching objective is a supervised enterprise department with explicit approvals and business-system writeback controls. The workflow is intentionally understandable and auditable before adding an autonomous code-generating ML agent. An AutoML or agentic research component could be evaluated later behind the same model-review and promotion gates.

## 8. Component replacement policy

Keep components behind clear interfaces:

- Replace the local synthetic connector with vendor APIs or a warehouse adapter.
- Replace SQLite LangGraph checkpoints with PostgreSQL-backed checkpoints.
- Replace Streamlit with an enterprise frontend without changing workflow stages.
- Replace scikit-learn with another modelling framework if the data type requires it.
- Replace Ollama with an approved managed provider or another local model runtime.
- Replace the local file artifact mount with approved object storage.

Before adopting a component commercially, check the exact version's licence, security advisories, model-weight licence, support status and infrastructure requirements. A framework can be open source while a particular model's weights or data may have separate restrictions.
