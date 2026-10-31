# Agentic ML Department

**A beginner-friendly, human-supervised AI department for a fictional business.** It connects to synthetic CRM, lead-generation, ERP/commerce, marketing and customer-support systems; profiles their data; proposes business questions; trains and compares prediction models; requests approvals; queues recommendations; writes approved scores back to a simulated CRM extension; and records outcomes so later training runs can learn from corrections.

> **What this is:** a runnable proof of concept and a reusable blueprint for a general enterprise Agentic AI SOP.
>
> **What this is not:** a production-ready autonomous decision-maker. All records are synthetic. The model is a demonstration, its scores are not validated on real operations, and no real business system is contacted.

## Source code is included

This repository contains the complete, readable Python implementation under `src/agentic_ml_department/`, the Streamlit dashboard under `dashboard/`, the synthetic-data setup script under `scripts/`, and automated tests under `tests/`. The `.source/` archive is a reproducible source snapshot, not an installer-only substitute. A GitHub Actions workflow expands that snapshot and commits the same source tree into normal repository paths.

## What you get

- A fictional company, **Northstar Office & Cloud**, with customers, leads, sales orders, support tickets and marketing campaigns.
- A PostgreSQL database, initialized with repeatable synthetic records.
- Business-system API simulators for CRM, lead generation, ERP/commerce, marketing automation and support.
- Exploratory data analysis across the five sources: schema/type discovery, samples, missingness, duplicates, numeric distribution summaries, category frequencies and top pairwise numeric associations.
- A LangGraph workflow with persisted checkpoints and three explicit human approval gates:
  1. Approve the business question before training.
  2. Review holdout metrics and approve model promotion.
  3. Approve score writeback before recommendations appear in the simulated CRM.
- Two working classification workflows: customer churn risk and lead conversion propensity.
- A model comparison (logistic regression vs. random forest), holdout evaluation, feature signals, model artifact storage and experiment tracking with MLflow.
- A Streamlit control room and a FastAPI API.
- Supervisor instructions, an outcome-feedback endpoint and a business-review record so the next approved run can learn from corrected labels.
- A plain-English SOP, architecture guide and step-by-step tutorial.

## Run it with Docker (recommended)

You do not need to know Python, SQL or machine learning to try the demonstration.

### Step 1 — Install Docker Desktop

Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) for your operating system and start it. Docker runs the database and the application in separate, preconfigured containers.

### Step 2 — Download this project

On the GitHub project page, choose **Code → Download ZIP**, extract it, and open a terminal in the extracted `agentic-ml-department` folder. Alternatively, if Git is installed:

```bash
git clone https://github.com/gaurav8b/agentic-ml-department.git
cd agentic-ml-department
```

Replace the placeholder account name with the account that owns the repository.

### Step 3 — Create your local settings file

Copy `.env.example` to `.env`.

- Windows PowerShell: `Copy-Item .env.example .env`
- macOS/Linux: `cp .env.example .env`

The included password is for a local demonstration only. Change it before exposing the project to any network or shared environment. Keep `.env` private; it is excluded from Git.

### Step 4 — Start the business and ML department

```bash
docker compose up --build -d
```

First startup downloads the required container images and Python packages. The project starts PostgreSQL, MLflow, the API and the dashboard. The database is automatically populated with fictional business records.

### Step 5 — Open the control room

| Service | Address | What it does |
|---|---|---|
| Business dashboard | http://localhost:8501 | Main screen for running the AI department and approving work |
| API documentation | http://localhost:8000/docs | Explore the API and synthetic business-system endpoints |
| Health check | http://localhost:8000/health | Confirm that the API can query the database |
| MLflow | http://localhost:5000 | See recorded model experiments and metrics |

### Step 6 — Run the first ML workflow

1. Choose **Customer churn risk** or **Lead conversion**.
2. Optionally provide an instruction, such as `Prioritize recall. Do not use satisfaction_score.`
3. Select **Start supervised ML workflow**.
4. Review the business question and approve it.
5. Review the candidate model's holdout metrics and feature signals. Approve or reject.
6. Review the records and destination in the writeback preview. Approve or reject.
7. Read the business-impact estimate and learning note.

The workflow pauses at every approval gate. Rejecting a gate stops the remaining workflow stages. Prediction records are queued internally during training; they are not marked as synchronized to the business-system simulator until the final writeback approval.

## What the demo predicts

| Business question | Source system | Outcome being learned | Example operational use |
|---|---|---|---|
| Which customers may leave? | CRM customer records, informed by support context in the business profile | Historical churn flag | Prioritize customer-success reviews |
| Which prospects may convert? | CRM / lead-generation records | Historical lead-conversion flag | Prioritize sales follow-up |

The synthetic source tables deliberately distinguish labelled historical rows from a separate current scoring population: 500 historical customers train churn models while 200 current customers are scored; 650 closed leads train conversion models while 250 open leads are scored. A scored entity is therefore not evaluated against a model that has already trained on that same row. Sales orders, support tickets and marketing campaigns are connected and profiled to demonstrate multi-system discovery, but are not silently used as model features. The next extensions can add approved joins, time-series demand forecasting, customer lifetime value and campaign attribution.

### Simulated business-system API endpoints

The FastAPI documentation at `/docs` lists these read-only source-system simulators and the synthetic CRM score destination:

| Simulated system | Endpoint |
|---|---|
| CRM customers | `GET /business/crm/customers` |
| CRM leads | `GET /business/crm/leads` |
| CRM prediction-score extension | `GET /business/crm/prediction-scores` |
| Lead generation | `GET /business/lead-generation/leads` |
| ERP / commerce orders | `GET /business/erp/orders` |
| Marketing campaigns | `GET /business/marketing/campaigns` |
| Customer support tickets | `GET /business/support/tickets` |

The ML department's main control endpoints include `POST /api/runs`, `POST /api/runs/{run_id}/resume`, `POST /api/outcomes`, `GET /api/monitoring` and `GET /api/agent-team`. All writes remain within the synthetic application database.

## Supervisor instructions

A supervisor can add instructions when starting a run. The prototype implements these controls deterministically:

- `prioritize recall` lowers the classification threshold to 0.35.
- `prioritize precision` raises the classification threshold to 0.65.
- `do not use <field_name>` or `exclude <field_name>` removes a named available feature.

For other instructions, the system records the guidance and includes it in the optional local language-model context. It does **not** pretend that arbitrary free text has been converted into a safe executable policy. Review `docs/APPROVALS_AND_GUARDRAILS.md` before adding new controls.

## Optional local language model

The demo works without an LLM key or cloud service. Its business-question suggestions use explicit rules by default.

To let LangChain call a local Ollama model:

1. Install [Ollama](https://ollama.com/download) on the host computer.
2. Download a model supported by your hardware, for example `ollama pull qwen3:8b`.
3. Change `.env` to `AGENT_LLM_PROVIDER=ollama`.
4. Set `OLLAMA_MODEL` to the exact model name you downloaded.
5. On Docker Desktop, `OLLAMA_BASE_URL=http://host.docker.internal:11434` usually lets the container reach Ollama on the host. On Linux, configure the host gateway as required by your Docker setup.
6. Restart the API: `docker compose up -d --build api`.

The local model only enriches the business-question advice in this prototype. It does not independently approve a model or write data to a business system.

## Stop the project

```bash
docker compose down
```

The database, LangGraph checkpoints, models and MLflow artifacts remain in the local project folders/volumes. To remove the Docker database volume and start with a completely fresh database:

```bash
docker compose down -v
```

**Warning:** `-v` removes the persisted PostgreSQL volume. Use it only when you intend to reset the demo.

## Learn how it works

Start with these documents, in order:

1. [`docs/START_HERE.md`](docs/START_HERE.md) — plain-English orientation and vocabulary.
2. [`docs/GENERAL_AGENTIC_AI_SOP.md`](docs/GENERAL_AGENTIC_AI_SOP.md) — the reusable enterprise SOP, written for a non-technical project owner.
3. [`docs/MAKE_THE_POC_LIVE.md`](docs/MAKE_THE_POC_LIVE.md) — the complete step-by-step SOP to bring the POC online and demonstrate it to a user.
4. [`docs/ML_DEPARTMENT_TUTORIAL.md`](docs/ML_DEPARTMENT_TUTORIAL.md) — the end-to-end machine-learning prototype walkthrough.
5. [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — components, data flow and system boundaries.
6. [`docs/LANGGRAPH_AND_LANGCHAIN.md`](docs/LANGGRAPH_AND_LANGCHAIN.md) — a code-level tutorial explaining how LangGraph and LangChain work in this project.
7. [`docs/MLZERO_COMPARISON.md`](docs/MLZERO_COMPARISON.md) — what we learn from AutoGluon Assistant / MLZero and what we intentionally do not copy.
8. [`docs/TECHNOLOGY_CHOICES.md`](docs/TECHNOLOGY_CHOICES.md) — why this open-source stack was selected and what can be replaced.
9. [`docs/APPROVALS_AND_GUARDRAILS.md`](docs/APPROVALS_AND_GUARDRAILS.md) — what the agents may and may not do.
10. [`docs/REAL_SYSTEM_INTEGRATION.md`](docs/REAL_SYSTEM_INTEGRATION.md) — replacing simulators with real company systems.
11. [`docs/OPERATIONS_AND_TROUBLESHOOTING.md`](docs/OPERATIONS_AND_TROUBLESHOOTING.md) — support, reset and test instructions.
12. [`docs/VALIDATION_REPORT.md`](docs/VALIDATION_REPORT.md) — what was tested and what still needs an end-to-end environment check.
13. [`docs/PUBLISH_TO_GITHUB.md`](docs/PUBLISH_TO_GITHUB.md) — historical instructions for publishing from a local checkout.

## Run tests locally (optional)

A Python 3.11+ environment is required. From the project folder:

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
pytest
```

The automated tests use a temporary SQLite database for repeatability. The main Docker demonstration uses PostgreSQL.

## Run from Python / CLI

After creating a Python 3.11+ virtual environment and installing `requirements.txt`:

```bash
pip install -e .
agentic-ml profile
agentic-ml run --objective customer_churn --instructions "Prioritize recall"
```

The CLI starts the same supervised LangGraph workflow as the dashboard and returns the first approval interrupt. Use the dashboard or the API resume endpoint to continue after each approval.

## Technology choices

- **LangGraph** — explicit workflow state, interrupt/resume approvals and checkpoints.
- **Specialist Python agents + tool registry** — data perception, task planning, safe tool selection and independent review through typed, testable Python functions.
- **LangChain** — model/provider integration for optional natural-language advice.
- **PostgreSQL + SQLAlchemy** — relational business data and application records.
- **scikit-learn** — transparent baseline classification pipelines.
- **MLflow** — experiment metrics, artifact lineage and comparison.
- **FastAPI** — documented interfaces to the department and synthetic business systems.
- **Streamlit** — the non-technical supervisor dashboard.
- **Ollama (optional)** — local model inference without a paid API key.

The stack is selected for an open-source, self-hostable proof of concept. Check project and dependency licences, hosting requirements and security advisories before adopting any component in a commercial environment.

## Important limitations

This is a proof of concept, not a claim that a real company can safely hand over every business function to autonomous agents. It uses generated data, simulated connectors, two supervised classification use cases and a basic learning-feedback loop. Production deployment requires real connector development, authentication and authorization, secrets management, privacy/legal review, robust monitoring, model validation, disaster recovery, human operating procedures and a named owner for each business action.
