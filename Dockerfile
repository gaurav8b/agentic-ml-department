FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt pyproject.toml README.md ./
COPY src ./src
COPY dashboard ./dashboard
RUN pip install --upgrade pip && pip install -r requirements.txt && pip install -e .

RUN mkdir -p /app/data /app/artifacts/models /app/artifacts/mlflow
EXPOSE 8000 8501 5000

CMD ["uvicorn", "agentic_ml_department.api:app", "--host", "0.0.0.0", "--port", "8000"]
