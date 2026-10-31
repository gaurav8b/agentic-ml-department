# Build and Validation Report

**Build date:** 2026-10-31  
**Project:** Agentic ML Department — Northstar Office & Cloud  
**Build type:** Local proof-of-concept source build

## What was verified in this build environment

| Check | Result | Evidence / scope |
|---|---|---|
| Python syntax compilation | Passed | `compileall` completed for application, dashboard, seed script and tests. |
| Synthetic database creation | Passed | Seeded 700 customers, 900 leads, 2,200 orders, 640 support tickets and 12 campaigns in a local SQLite test database. |
| Business connector inventory | Passed | Five simulated systems and 4,452 total source records verified. |
| Exploratory profile generation | Passed | Tests verify numeric summaries and non-causal numeric-association output. |
| Customer-churn training | Passed | Two candidate classifiers trained and evaluated; current customers scored separately from historical training records. |
| Lead-conversion training | Passed | Closed historical leads used for training; separate open leads scored. |
| Supervisor training controls | Passed | Recall/precision thresholds and named feature exclusion exercised by tests. |
| Business impact threshold | Passed | Test confirms impact summary applies the prediction-specific threshold. |
| Outcome feedback to later training cohort | Passed | Test confirms a newly labelled customer moves into the future historical cohort. |
| Automated tests | Passed | `7 passed` using SQLite. |
| Compose and CI YAML syntax | Passed | Both YAML files parsed successfully with PyYAML. |

## What was not run end-to-end here

- **Docker Compose services:** the Docker CLI/daemon is not available in this build environment, so PostgreSQL, MLflow, FastAPI and Streamlit were not started as a container stack.
- **Full dependency installation:** package installation was attempted but the package index could not be reached from this environment. As a result, LangGraph, LangChain, LangChain-Ollama, MLflow, Streamlit and psycopg were not installed here.
- **LangGraph interrupt/resume execution:** the approval graph is implemented in source and follows the documented `interrupt`/`Command(resume=...)` pattern, but the graph itself could not be executed without the LangGraph packages.
- **PostgreSQL and MLflow service connections:** configuration and Compose YAML were inspected, but live connections were not tested.
- **Optional Ollama adviser:** no local Ollama server/model was available, so the no-LLM deterministic path is the only one tested at runtime.
- **Real business integrations:** no real CRM, ERP, marketing, support or lead-generation system was contacted. All connectors in this project are synthetic simulators.
- **Remote GitHub publication:** the connected GitHub integration can inspect and edit existing repositories but does not offer a create-repository operation. Follow `PUBLISH_TO_GITHUB.md` to create the empty remote repository and push this checked local project.

## Re-run the locally available checks

From the repository root in a Python 3.11+ environment:

```bash
python -m compileall -q src dashboard scripts tests
DATABASE_URL=sqlite:///./test_agentic_ml.db AUTO_SEED_DEMO=false MLFLOW_TRACKING_URI= pytest -q
```

The GitHub Actions workflow `.github/workflows/tests.yml` installs the full requirements, installs this package and runs the test suite on pushes and pull requests to `main`.

## Release gate before calling this a working deployment

1. Install dependencies successfully in a clean Python 3.12/Docker environment.
2. Run `docker compose up --build -d` and confirm database, MLflow, API and dashboard health.
3. Execute all three approval paths: approve, reject, and approve model/reject writeback.
4. Restart the API between an approval pause and resume; confirm the LangGraph checkpoint resumes correctly.
5. Verify MLflow records and artifact downloads from the browser.
6. Test local Ollama only if the optional adviser is enabled.
7. Review security, identity, data privacy and operational controls before any real connector is introduced.

A local source test pass is not equivalent to a verified container deployment or production readiness.
