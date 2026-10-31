# Operations and Troubleshooting

## Start and inspect services

```bash
docker compose up --build -d
docker compose ps
docker compose logs -f --tail=200
```

Check health:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/systems
curl http://localhost:8000/api/profiles
```

## Common problems

### Docker command not found

Install Docker Desktop and start it. Then reopen the terminal and verify `docker --version` and `docker compose version`.

### Dashboard says it cannot reach the API

Run `docker compose ps` and inspect the API logs with `docker compose logs -f api`. Wait for the database and MLflow health checks to pass. The API container must be healthy before the dashboard starts.

### Database connection failure

Check `.env` values. `DATABASE_URL` must use the same database username, password, host service name (`db`), port and database name as the Compose configuration. The database host inside the Compose network is `db`, not `localhost`.

### First startup takes a while

Docker must download images and install several Python packages. This is a one-time setup unless the dependencies or images change.

### Ollama advice is missing

The workflow works without Ollama. Confirm `AGENT_LLM_PROVIDER=ollama`, that the model is installed locally and that the container can reach the Ollama server. If Ollama is unavailable, the deterministic business-question suggestions still work.

### Model quality gate fails

This can happen because the selected demonstration data or the candidate model does not pass the prototype threshold. Do not assume it is safe. Reject the candidate or provide a meaningful documented override reason only for a controlled experiment. A production quality gate must be based on business error costs, test design and risk review.

### A run is waiting for approval

This is expected. Find it in the approval inbox and approve or reject it. The graph checkpoint preserves the workflow thread while it waits.

### A run is stopped

A human rejected an approval gate, or the model gate required an override reason that was not supplied. Start a new run after reviewing the relevant issue. The workflow does not continue past a rejected approval.

## Reset demo data

To reset the synthetic business tables without deleting the Docker database volume, call:

```bash
curl -X POST "http://localhost:8000/api/demo/seed?force=true"
```

This re-seeds the business tables. It does not clear workflow history, model artifacts or feedback. For a full clean demo, stop the project and remove the database volume:

```bash
docker compose down -v
```

The project folder's `data/` and `artifacts/` directories are not Docker database volumes; move or delete them separately only when you deliberately want to remove checkpoints and files.

## Run automated tests

```bash
python -m venv .venv
# Activate the virtual environment for your operating system.
pip install -r requirements.txt
pip install -e .
pytest
```

## Backup checklist

Before any real-data pilot, define backups for:

- PostgreSQL data.
- LangGraph checkpoint data.
- Model files and MLflow artifacts.
- Application configuration and versioned workflow source.
- Approval and audit records.

Test restoration. A backup that has never been restored is not a proven recovery plan.
