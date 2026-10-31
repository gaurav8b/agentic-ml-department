"""Environment-backed configuration for the local demonstration."""
from __future__ import annotations

import os
from pathlib import Path

# Checkpoint deserialization must reject unknown object types. State values are JSON-like data.
os.environ.setdefault("LANGGRAPH_STRICT_MSGPACK", "true")

ROOT = Path(__file__).resolve().parents[2]


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{(ROOT / 'data' / 'agentic_ml.db').as_posix()}"
    )
    langgraph_checkpoint_path: Path = Path(
        os.getenv("LANGGRAPH_CHECKPOINT_PATH", str(ROOT / "data" / "checkpoints.sqlite"))
    )
    model_artifact_dir: Path = Path(
        os.getenv("MODEL_ARTIFACT_DIR", str(ROOT / "artifacts" / "models"))
    )
    mlflow_tracking_uri: str | None = os.getenv("MLFLOW_TRACKING_URI")
    agent_llm_provider: str = os.getenv("AGENT_LLM_PROVIDER", "none").lower()
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen3:8b")
    auto_seed_demo: bool = env_bool("AUTO_SEED_DEMO", True)


settings = Settings()
settings.langgraph_checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
settings.model_artifact_dir.mkdir(parents=True, exist_ok=True)
