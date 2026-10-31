# Agentic ML Department

A supervised, approval-led agentic machine-learning department reference implementation. This repository contains the complete runnable project, synthetic business-system simulators, seeded datasets, APIs, Streamlit control room, tests, Docker setup, and detailed beginner-friendly implementation guides.

## Get started

Clone the repository, then run the extraction helper for your operating system.

**Linux / macOS**
```bash
bash extract-source.sh
cd agentic-ml-department
cp .env.example .env
docker compose up --build -d
```

**Windows PowerShell**
```powershell
.\extract-source.ps1
Set-Location agentic-ml-department
Copy-Item .env.example .env
docker compose up --build -d
```

The helpers reconstruct and checksum-verify the compressed source bundle from the numbered base64 parts under `.source/parts/`, then extract the full project. You do not need to manually assemble the parts.

Open the business control room at http://localhost:8501, API documentation at http://localhost:8000/docs, and MLflow at http://localhost:5000.

## What the prototype demonstrates

- Five synthetic business systems: CRM, lead generation, ERP/commerce, customer support, and marketing automation.
- PostgreSQL as the persistence layer.
- Exploratory data analysis with missingness, duplicates, distributions, category frequencies, and numeric associations.
- Two predictive workflows: customer churn risk and lead conversion propensity.
- Historical training cohorts separated from current scoring populations.
- Human approval gates for business questions, model promotion, and business-system writeback.
- Supervisor instructions and bounded policy adjustments.
- Verified outcome feedback for future training runs.
- MLflow experiment tracking and a Streamlit business-user control room.

## Technology stack

LangGraph orchestrates stateful workflows and approval gates. LangChain provides optional language-model and tool integrations. Ollama is an optional local model provider. PostgreSQL stores business and workflow data. pandas, NumPy and scikit-learn implement the analytics and modelling pipeline. MLflow tracks experiments. FastAPI exposes services, Streamlit provides the control room, and Docker Compose runs the local stack.

The default synthetic demonstration does not require a paid LLM API key. Real production integrations require connector-specific authentication, authorization, data contracts, security review, and human-approved writeback.

## Beginner's guide

After extraction, start with `agentic-ml-department/docs/START_HERE.md`, then read:

1. `docs/GENERAL_AGENTIC_AI_SOP.md` — reusable enterprise SOP.
2. `docs/ML_DEPARTMENT_TUTORIAL.md` — step-by-step ML department walkthrough.
3. `docs/ARCHITECTURE.md` — system components and data flow.
4. `docs/LANGGRAPH_AND_LANGCHAIN.md` — orchestration and LLM integration tutorial.
5. `docs/APPROVALS_AND_GUARDRAILS.md` — approvals, safety boundaries and control.
6. `docs/REAL_SYSTEM_INTEGRATION.md` — how to replace simulators with actual business systems.
7. `docs/OPERATIONS_AND_TROUBLESHOOTING.md` — operating and debugging the demo.

## Scope and limitations

This is a proof-of-concept, not an autonomous production department. Business-system connectors are synthetic simulators. Human approval is mandatory for model promotion and outbound writes. Predictions are decision support, not guaranteed outcomes. The validation report distinguishes automated source tests from full live-stack verification.

## License

Apache-2.0. See [LICENSE](LICENSE).
