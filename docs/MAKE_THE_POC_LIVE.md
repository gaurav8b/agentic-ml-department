# Standard Operating Procedure: Make the Agentic ML Department POC Live

**Audience:** business owner, project sponsor, demonstration host or first-time operator  
**Purpose:** bring the complete Northstar Office & Cloud proof of concept online and demonstrate its full supervised machine-learning lifecycle.  
**Expected time:** allow time for the first Docker image build and the first model-training run; later starts are normally faster.  
**Environment:** one laptop or workstation with Docker Desktop / Docker Engine and Docker Compose.

> **Important boundary:** this procedure starts a local demonstration using fictional data and simulated CRM, lead-generation, ERP, marketing and support systems. It does not connect to a real company, send messages to customers, change real CRM records or make autonomous business decisions. Do not expose this demo to the public internet.

## 1. What the audience will see

When the POC is live, the operator can show one end-to-end workflow:

1. The application discovers five synthetic business systems and profiles their data.
2. The specialist-agent workflow describes business questions that could be answered from the available data.
3. A human approves the specific question before the model-training work starts.
4. The ML pipeline trains and compares candidate models, evaluates them on a holdout sample and presents the results.
5. A human reviews and approves (or rejects) model promotion.
6. The system prepares a preview of the prediction records and destination. A human separately approves (or rejects) simulated CRM writeback.
7. The dashboard displays the resulting business review and learning note.
8. The operator can record a verified synthetic outcome. That feedback is available to later approved training runs; the system does not silently change its own policy.

Two demonstrations are available: **customer churn risk** and **lead conversion propensity**.

## 2. Pre-flight checklist

Before the meeting, confirm:

- Docker Desktop is installed and running (Windows/macOS), or Docker Engine and the Docker Compose plugin are installed and running (Linux).
- Git is installed if you plan to clone rather than download the GitHub ZIP.
- The workstation has a reliable internet connection for the first image and package downloads.
- No other local application is already using ports `5000`, `8000` or `8501`.
- The project folder is writable; the application persists local database, checkpoint, model and MLflow files under the project folder and Docker volume.
- You have not placed a real `.env` file, credential or customer dataset into the public GitHub repository.

No paid LLM key is required. The default deterministic adviser and the model-training demonstrations work without Ollama or any external AI API key.

## 3. Get the project onto the workstation

### Option A — clone the GitHub repository (recommended)

Open Terminal, PowerShell or Command Prompt and run:

```bash
git clone https://github.com/gaurav8b/agentic-ml-department.git
cd agentic-ml-department
```

### Option B — download a ZIP

Open the repository page:

<https://github.com/gaurav8b/agentic-ml-department>

Choose **Code → Download ZIP**, extract it, and open a terminal in the extracted `agentic-ml-department` folder. The complete source tree should be present alongside `README.md`, `Dockerfile` and `docker-compose.yml` (the source archive remains available under `.source/` as a reproducible source snapshot).

## 4. Configure the local demonstration

Create `.env` from the supplied example file.

**Windows PowerShell:**

```powershell
Copy-Item .env.example .env
```

**macOS / Linux:**

```bash
cp .env.example .env
```

The example uses a local-only demonstration password. It is acceptable only for a private localhost demonstration. Do not reuse it for a shared deployment, do not publish `.env`, and do not expose the database or application ports to the internet. The `.gitignore` file excludes `.env` from source control.

The default settings use PostgreSQL, the local MLflow tracking service and synthetic data seeding. `AGENT_LLM_PROVIDER=none` is intentional: no LLM setup is needed to demonstrate the workflow. Leave it unchanged for the first run.

## 5. Validate and start the services

From the project root, validate the Compose configuration:

```bash
docker compose config
```

Then build and start all services:

```bash
docker compose up --build -d
```

The stack contains four services:

| Service | Role | Local address |
|---|---|---|
| `db` | PostgreSQL business and workflow database | Internal to Docker Compose |
| `api` | FastAPI control plane, synthetic system connectors and workflow endpoints | <http://localhost:8000> |
| `dashboard` | Streamlit control room for a non-technical supervisor | <http://localhost:8501> |
| `mlflow` | Model experiment and metric tracking | <http://localhost:5000> |

The API waits for PostgreSQL and MLflow health checks. The dashboard waits for the API health check. On first launch, allow containers to download/build and for the synthetic data to seed.

Check service status:

```bash
docker compose ps
```

Check the API health endpoint:

```bash
curl http://localhost:8000/health
```

A healthy response should include `"status":"ok"`, the fictional company name and `"database":"connected"`. On Windows PowerShell, `Invoke-RestMethod http://localhost:8000/health` is an alternative to `curl`.

If a service is still starting, inspect its logs:

```bash
docker compose logs --tail=150 api db mlflow dashboard
```

Do not continue to the live demonstration until `api` is healthy and the dashboard can load.

## 6. Open the control room

Open these pages in a browser:

- **Main demonstration:** <http://localhost:8501>
- **Interactive API reference:** <http://localhost:8000/docs>
- **Health check:** <http://localhost:8000/health>
- **MLflow experiments:** <http://localhost:5000>

On the dashboard, first point out the source-system cards and record counts. Expand the profiles to show discovered fields, missing values, duplicate counts, summary statistics and numeric associations. Make clear that the associations are descriptive and do not establish causation.

The example company is Northstar Office & Cloud. Its sources are synthetic CRM customers, lead-generation leads, ERP/commerce orders, customer-support tickets and marketing campaigns.

## 7. Run the main demonstration

### 7.1 Start a customer-churn workflow

1. In **1. Start a business question**, select **Customer churn risk — identify customers who may leave**.
2. In the supervisory-instructions box, enter an example instruction such as:

   `Prioritize recall. Do not use satisfaction_score. Explain the trade-off before promoting the model.`

3. Click **Start supervised ML workflow**.
4. The run should appear in the **Approval inbox** awaiting a business-question decision.

### 7.2 Approval gate 1 — business question

Explain that the system has profiled the available data, selected permitted tools and prepared a plan. Expand **Agent-generated execution plan** and **Allow-listed tools selected for this workflow** to show how the work is scoped.

Review the proposed business questions and data note. Add comments where useful, then choose one of:

- **Approve and continue** to authorize this question and proceed to the modelling stage.
- **Reject / stop** to demonstrate that the workflow can be stopped by a human.

A rejection is a valid demonstration outcome. To continue the main happy-path demonstration after a rejection, start a fresh run.

### 7.3 Approval gate 2 — model promotion

After training and evaluation complete, the inbox presents the candidate model and holdout metrics, including ROC AUC, PR AUC, precision and recall, as well as the independent automated-review notes and feature signals where available.

Explain the trade-offs rather than presenting one metric as universally best. The dashboard displays the quality-gate result. If the quality gate fails, the UI requires a documented override reason before proceeding; a comment cannot bypass the structural checks carried out by the workflow.

Choose **Approve and continue** to allow the candidate to be promoted in this demo, or **Reject / stop** to stop the run. Approval here does not yet authorize writeback.

### 7.4 Approval gate 3 — business-system writeback

The system now displays a preview of prediction records and the simulated destination. Emphasize that the scores are queued and remain unsynchronized until this separate approval.

- Choose **Approve and continue** to write the approved scores to the synthetic CRM prediction-score extension.
- Choose **Reject / stop** to demonstrate that model approval and business-system writeback are distinct decisions.

After approval, the run should complete. The **Agent activity and run history** section shows the specialist-agent execution trace and run details. The business-review section shows a simulated impact summary and a learning note.

### 7.5 Inspect the result in the synthetic CRM and MLflow

Use the API docs to call:

- `GET /business/crm/prediction-scores` — approved and synchronized synthetic scores.
- `GET /api/predictions` — prediction records and synchronization state.
- `GET /api/models` — registered model metadata and metrics.
- `GET /api/monitoring` — observed outcome monitoring summary.

Open MLflow at <http://localhost:5000> to inspect the tracked experiment and metrics. These are results from synthetic data, not evidence of real-world model effectiveness.

### 7.6 Record feedback (optional)

After the third approval, the dashboard's **Record a verified outcome** section allows the operator to choose a synchronized prediction and record whether the event actually occurred, with a reviewer note. Only enter a result that has actually been verified in the demo scenario. The feedback is matched to the synchronized prediction and can become historical training data for a later approved run.

This is a controlled feedback loop, not automatic self-modification: the next training run still requires a fresh business-question approval and model-promotion approval.

## 8. Demonstrate lead conversion

Repeat Section 7 with **Lead conversion — prioritize prospects most likely to buy**. For example, a supervisor instruction can be:

`Prioritize precision. Exclude company_size.`

Use the three approvals again. The business-use explanation is that sales teams could prioritize follow-up on a ranked list of prospects. The scores are probability estimates, not promises that a lead will convert.

## 9. Useful API pages for a guided technical tour

The interactive page <http://localhost:8000/docs> documents the endpoints. The principal endpoints include:

| Endpoint | What to show |
|---|---|
| `GET /api/systems` | Available synthetic source systems and status |
| `GET /api/profiles` | Data profiling summary |
| `GET /api/agent-team` | Agent roles and execution policy |
| `POST /api/runs` | Start a supervised workflow |
| `GET /api/runs` and `GET /api/runs/{run_id}` | Run status, approval state and agent trace |
| `POST /api/runs/{run_id}/resume` | Record an approval or rejection |
| `GET /api/models` | Model metadata and metrics |
| `GET /api/predictions` | Prediction queue and sync state |
| `POST /api/outcomes` | Record a verified outcome through the API |
| `GET /api/monitoring` | Compare synchronized predictions with observed outcomes |

Use the dashboard for the live presentation; the API docs are best for explaining the underlying interface and inspecting the JSON responses.

## 10. End the demonstration safely

Stop the containers but preserve the database and local artifacts:

```bash
docker compose down
```

To restart later:

```bash
docker compose up -d
```

To completely reset the demo database and start again from a clean synthetic dataset:

```bash
docker compose down -v
docker compose up --build -d
```

**Warning:** `docker compose down -v` deletes the PostgreSQL data volume. Do not run this command if you need to keep the run history, approval decisions, recorded outcomes or database state. The local `data/` and `artifacts/` directories should also be handled carefully if you intend to preserve checkpoints or model artifacts.

## 11. Troubleshooting

| Symptom | What to do |
|---|---|
| Dashboard says it cannot reach the API | Run `docker compose ps`, check `docker compose logs api`, and verify <http://localhost:8000/health>. |
| API reports database unavailable | Check `docker compose logs db api`; wait for PostgreSQL health status. Confirm `.env` and the Compose database URL use the same local password. |
| Port is already allocated | Stop the other local application using `5000`, `8000` or `8501`, then restart Compose. |
| Image build or package downloads fail | Check internet connectivity and Docker Desktop/Engine status, then retry `docker compose up --build -d`. |
| MLflow page is not ready | Run `docker compose logs mlflow`; wait for the MLflow service health check and try again. |
| A workflow is waiting for an approval | This is expected. Review the pending gate and approve or reject it in the dashboard. |
| A run failed unexpectedly | Inspect the run details in the dashboard and run `docker compose logs --tail=200 api`. Do not approve a result whose evidence you cannot understand. |
| Need a clean demonstration | Use the reset commands in Section 10 only when deleting previous demo state is acceptable. |

## 12. Demonstration acceptance checklist

The POC is ready to show when all of the following are true:

- [ ] `docker compose ps` shows the services running/healthy.
- [ ] `http://localhost:8000/health` confirms the database connection.
- [ ] `http://localhost:8501` opens and displays the five synthetic system cards.
- [ ] The source profiles can be expanded and inspected.
- [ ] A customer-churn or lead-conversion run can be started.
- [ ] The business-question approval appears and can be approved or rejected.
- [ ] Model metrics and independent review evidence appear at the second gate.
- [ ] The separate writeback preview appears at the third gate.
- [ ] After writeback approval, synchronized predictions are visible in the synthetic CRM/API.
- [ ] Run history, agent trace and MLflow experiment information can be inspected.

A local POC that passes this checklist is a successful demonstration of the supervised workflow. It is **not** a production readiness certification. Before any real business use, implement real connector authentication and authorization, secrets management, data privacy controls, model risk review, observability, backups, disaster recovery, security testing and named human ownership for every business action.
