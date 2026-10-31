"""Small, auditable specialist agents inspired by MLZero's role separation.

These agents perform constrained analysis and planning. They do not execute generated code.
"""
from __future__ import annotations

from typing import Any

from ..modeling import OBJECTIVES
from ..tool_registry import ToolRegistry


def run_data_perception(profiles: list[dict]) -> dict[str, Any]:
    compact = []
    warnings = []
    for profile in profiles:
        fields = profile.get("fields", [])
        high_missing = [f["name"] for f in fields if profile.get("rows", 0) and f.get("missing", 0) / profile["rows"] >= 0.20]
        if high_missing:
            warnings.append({"source": profile.get("source"), "fields_with_20pct_missing": high_missing})
        compact.append({
            key: profile.get(key)
            for key in ("source", "rows", "columns", "missing_cells", "duplicate_rows", "fields", "top_numeric_correlations", "correlation_note")
            if key in profile
        })
    return {
        "profiles": compact,
        "quality_warnings": warnings,
        "trace": {
            "agent": "data_perception_agent",
            "status": "completed",
            "summary": f"Profiled {len(compact)} sources; found {len(warnings)} source(s) with fields missing at least 20% of values.",
            "outputs": {"source_count": len(compact), "quality_warning_count": len(warnings)},
        },
    }


def run_task_planner(objective: str, profiles: list[dict], instructions: str = "") -> dict[str, Any]:
    if objective not in OBJECTIVES:
        raise ValueError(f"Unsupported objective: {objective}")
    spec = OBJECTIVES[objective]
    plan = [
        {"step": 1, "owner": "data_perception_agent", "action": "Inspect available source tables, schema, missingness and duplicates", "approval_required": False},
        {"step": 2, "owner": "business_question_agent", "action": "Present the proposed business outcome and request supervisor approval", "approval_required": True},
        {"step": 3, "owner": "ml_execution_agent", "action": "Train and compare fixed baseline models using historical labelled records", "approval_required": False},
        {"step": 4, "owner": "model_review_agent", "action": "Review holdout metrics, cohort separation and candidate model quality", "approval_required": True},
        {"step": 5, "owner": "business_integration_agent", "action": "Preview and synchronize approved scores to the synthetic business system", "approval_required": True},
        {"step": 6, "owner": "business_feedback_agent", "action": "Collect verified outcomes and report measured business indicators", "approval_required": False},
    ]
    data_sources = [p.get("source") for p in profiles]
    return {
        "plan": {
            "objective": objective,
            "business_question": spec["business_question"],
            "business_value": spec["business_value"],
            "steps": plan,
            "discovered_sources": data_sources,
            "supervisor_instructions": instructions,
            "constraints": [
                "No generated Python or shell code is executed.",
                "No model is promoted before model approval.",
                "No business-system writeback occurs before writeback approval.",
                "Predictions are decision support, not guaranteed outcomes.",
            ],
        },
        "trace": {"agent": "task_descriptor_agent", "status": "completed", "summary": f"Created a {len(plan)}-step plan for {spec['label']}.", "outputs": {"step_count": len(plan), "source_count": len(data_sources)}},
    }


def run_tool_selector(objective: str, registry: ToolRegistry) -> dict[str, Any]:
    if objective not in OBJECTIVES:
        raise ValueError(f"Unsupported objective: {objective}")
    available = registry.describe()
    selected_names = ["discover_business_systems", "create_training_candidate", "sync_approved_predictions"]
    selected = [tool for tool in available if tool["name"] in selected_names]
    return {
        "selected_tools": selected,
        "trace": {
            "agent": "tool_selector_agent",
            "status": "completed",
            "summary": f"Selected {len(selected)} allow-listed tools; {sum(t['requires_human_approval'] for t in selected)} require explicit approval.",
            "outputs": {"selected_tool_names": [t["name"] for t in selected]},
        },
    }


def run_reviewer(model_result: dict, quality_gate_passed: bool) -> dict[str, Any]:
    metrics = model_result.get("metrics", {})
    checks = {
        "holdout_rows_present": int(metrics.get("rows_evaluated", 0)) > 0,
        "historical_training_rows_present": int(metrics.get("rows_available", 0)) > 0,
        "separate_current_rows_scored": int(metrics.get("rows_scored", 0)) > 0,
        "candidate_has_artifact_reference": bool(model_result.get("artifact_path")),
    }
    passed = all(checks.values())
    review = {
        "passed": passed,
        "business_quality_gate_passed": bool(quality_gate_passed),
        "checks": checks,
        "reviewer_summary": "Structural evidence checks passed; human model-promotion approval is still required." if passed and quality_gate_passed else ("Structural evidence checks passed, but the candidate does not meet the model quality gate; a documented human override is required." if passed else "One or more structural evidence checks failed. The candidate must not be promoted."),
        "limitations": ["Synthetic data only", "Holdout metrics do not establish business value", "Feature importance is not causal explanation"],
    }
    return {
        "review": review,
        "trace": {"agent": "model_review_agent", "status": "completed", "summary": review["reviewer_summary"], "outputs": {"passed": passed, "checks": checks}},
    }
