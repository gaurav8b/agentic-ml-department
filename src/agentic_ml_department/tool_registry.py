"""Explicit allow-list for agent-callable business and ML tools.

The registry exposes fixed Python functions, never arbitrary shell or generated-code execution.
Every tool has a stable name, description, risk class, and input schema metadata.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    risk: str
    handler: Callable[..., Any]
    input_fields: tuple[str, ...] = ()
    requires_human_approval: bool = False


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        if spec.name in self._tools:
            raise ValueError(f"Tool already registered: {spec.name}")
        self._tools[spec.name] = spec

    def get(self, name: str) -> ToolSpec:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"Tool is not allow-listed: {name}") from exc

    def describe(self) -> list[dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "risk": tool.risk,
                "input_fields": list(tool.input_fields),
                "requires_human_approval": tool.requires_human_approval,
            }
            for tool in self._tools.values()
        ]

    def invoke(self, name: str, *, approved: bool = False, **kwargs: Any) -> Any:
        tool = self.get(name)
        if tool.requires_human_approval and not approved:
            raise PermissionError(f"Tool {name!r} requires explicit human approval")
        unexpected = set(kwargs) - set(tool.input_fields)
        missing = set(tool.input_fields) - set(kwargs)
        if unexpected or missing:
            raise ValueError(f"Invalid arguments for {name}: missing={sorted(missing)}, unexpected={sorted(unexpected)}")
        return tool.handler(**kwargs)


def build_default_registry() -> ToolRegistry:
    """Build safe demo tools. Read-only tools have no side effects; writeback is guarded."""
    from .connectors import business_system_summary

    registry = ToolRegistry()
    registry.register(ToolSpec(
        name="discover_business_systems",
        description="List connected synthetic business systems, record counts and data profiles.",
        risk="read_only",
        handler=business_system_summary,
    ))
    registry.register(ToolSpec(
        name="create_training_candidate",
        description="Train the approved churn or lead-conversion objective and queue scores internally.",
        risk="model_development",
        handler=_train_candidate,
        input_fields=("objective", "run_id", "supervisor_instructions"),
    ))
    registry.register(ToolSpec(
        name="sync_approved_predictions",
        description="Synchronize queued prediction scores to the synthetic CRM extension after approval.",
        risk="external_write",
        handler=_sync_predictions,
        input_fields=("run_id",),
        requires_human_approval=True,
    ))
    return registry


def _train_candidate(objective: str, run_id: str, supervisor_instructions: str = "") -> dict:
    from .modeling import train_and_score
    return train_and_score(objective, run_id, supervisor_instructions)


def _sync_predictions(run_id: str) -> dict:
    from .modeling import sync_predictions
    return sync_predictions(run_id)
