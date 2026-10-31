"""LangGraph state machine for the supervised ML-department lifecycle.

The graph deliberately mixes deterministic business logic with optional LLM advice.
Irreversible business-system writeback is protected by an explicit approval interrupt.
"""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any, TypedDict

# Restrict checkpoint deserialization to safe, expected primitive data.
os.environ.setdefault("LANGGRAPH_STRICT_MSGPACK", "true")

from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command, interrupt

from .advisor import build_business_questions
from .agents import run_data_perception, run_task_planner, run_tool_selector, run_reviewer
from .tool_registry import build_default_registry
from .config import settings
from .connectors import business_system_summary
from .db import SessionLocal
from .modeling import (OBJECTIVES, activate_model, calculate_business_impact,
                       sync_predictions, train_and_score)
from .models import BusinessReview, ModelRecord, SupervisorInstruction, WorkflowRecord


class MLDepartmentState(TypedDict, total=False):
    run_id: str
    objective: str
    supervisor_instructions: str
    business_snapshot: dict
    data_profiles: list[dict]
    agent_trace: list[dict]
    task_plan: dict
    selected_tools: list[dict]
    review_result: dict
    business_question_proposal: dict
    question_approval: dict
    model_result: dict
    model_approval: dict
    writeback_approval: dict
    writeback_result: dict
    business_impact: dict
    learning_note: str
    workflow_result: dict
    error: str


settings.langgraph_checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
_checkpoint_connection = sqlite3.connect(str(settings.langgraph_checkpoint_path), check_same_thread=False)
_checkpointer = SqliteSaver(_checkpoint_connection)
_checkpointer.setup()


def _discover(state: MLDepartmentState) -> dict:
    """Find the connected systems and source record counts."""
    return {"business_snapshot": business_system_summary()}


def _profile(state: MLDepartmentState) -> dict:
    """Data-perception agent: summarize quality, schema and analytical affordances."""
    snapshot = state.get("business_snapshot", {})
    profiles = snapshot.get("profiles", [])
    perception = run_data_perception(profiles)
    return {"data_profiles": perception["profiles"], "agent_trace": state.get("agent_trace", []) + [perception["trace"]]}


def _plan_tasks(state: MLDepartmentState) -> dict:
    """Task-descriptor agent: create an auditable plan from the approved objective."""
    plan = run_task_planner(state["objective"], state.get("data_profiles", []),
                            state.get("supervisor_instructions", ""))
    return {"task_plan": plan["plan"], "agent_trace": state.get("agent_trace", []) + [plan["trace"]]}


def _select_tools(state: MLDepartmentState) -> dict:
    """Tool-selector agent: select only pre-registered, allow-listed Python tools."""
    registry = build_default_registry()
    selection = run_tool_selector(state["objective"], registry)
    return {"selected_tools": selection["selected_tools"],
            "agent_trace": state.get("agent_trace", []) + [selection["trace"]]}


def _propose_questions(state: MLDepartmentState) -> dict:
    proposal = build_business_questions(
        state["objective"], state.get("business_snapshot", {}).get("profiles", []),
        state.get("supervisor_instructions", ""),
    )
    proposal["task_plan"] = state.get("task_plan", {})
    proposal["selected_tools"] = state.get("selected_tools", [])
    return {"business_question_proposal": proposal}


def _question_gate(state: MLDepartmentState) -> dict:
    """Pause until a person approves the proposed business problem."""
    answer = interrupt({
        "approval_type": "business_question",
        "title": "Approve the business question",
        "instruction": "Review the proposed question. Approve to allow model development, or reject/request changes.",
        "proposal": state.get("business_question_proposal", {}),
        "risk": "No model is trained and no business system is changed before this approval.",
    })
    return {"question_approval": answer}


def _route_question(state: MLDepartmentState) -> str:
    return "train" if state.get("question_approval", {}).get("approved") else "stop"


def _train(state: MLDepartmentState) -> dict:
    initial_instruction = state.get("supervisor_instructions", "")
    approval_comments = state.get("question_approval", {}).get("comments", "")
    combined_instruction = "\n".join(x for x in (initial_instruction, approval_comments) if x.strip())
    result = train_and_score(state["objective"], state["run_id"], combined_instruction)
    return {"model_result": result,
            "agent_trace": state.get("agent_trace", []) + [{
                "agent": "ml_execution_agent", "status": "completed",
                "summary": f"Trained {len(result.get('metrics', {}).get('model_candidates', []))} candidate pipelines and scored {result.get('predictions_queued', 0)} records.",
                "artifact": result.get("artifact_path"),
            }]}


def _model_gate(state: MLDepartmentState) -> dict:
    result = state.get("model_result", {})
    metrics = result.get("metrics", {})
    # A simple minimum bar for this teaching demo; humans may reject a passing model.
    enough_data = metrics.get("rows_available", 0) >= OBJECTIVES[state["objective"]]["minimum_rows"]
    auc = metrics.get("roc_auc", 0.0)
    quality_passed = bool(enough_data and auc >= 0.60)
    review = run_reviewer(result, quality_passed)
    answer = interrupt({
        "approval_type": "model_promotion",
        "title": "Review the candidate model",
        "instruction": "Inspect the holdout metrics and feature signals. Approve to promote it to ACTIVE, or reject it.",
        "candidate": result,
        "quality_gate": {
            "passed": quality_passed,
            "minimum_rows": OBJECTIVES[state["objective"]]["minimum_rows"],
            "minimum_roc_auc": 0.60,
            "message": "The prototype's minimum quality rule passed." if quality_passed else "The candidate is below the demo quality bar. Reject it or provide a documented override reason.",
        },
        "automated_review": review["review"],
        "risk": "The model has only been evaluated on synthetic data. Approval does not authorize real-money or high-impact automated decisions.",
    })
    return {"model_approval": {**answer, "quality_gate_passed": quality_passed},
            "review_result": review["review"],
            "agent_trace": state.get("agent_trace", []) + [review["trace"]]}


def _route_model(state: MLDepartmentState) -> str:
    decision = state.get("model_approval", {})
    if not decision.get("approved"):
        return "stop"
    if not state.get("review_result", {}).get("passed", False):
        return "stop"
    quality_passed = decision.get("quality_gate_passed", False)
    override = str(decision.get("comments", "")).strip()
    if not quality_passed and len(override) < 15:
        return "stop"
    return "promote"


def _promote_model(state: MLDepartmentState) -> dict:
    model_ref = state["model_result"]["model_ref"]
    activate_model(model_ref)
    return {"model_promotion": {"model_ref": model_ref, "status": "ACTIVE"}}


def _writeback_gate(state: MLDepartmentState) -> dict:
    result = state.get("model_result", {})
    answer = interrupt({
        "approval_type": "business_system_writeback",
        "title": "Approve CRM / lead-system writeback",
        "instruction": "This is the final approval before prediction scores are marked as synchronized to the synthetic CRM extension.",
        "preview": {
            "objective": state["objective"],
            "records_to_sync": result.get("predictions_queued", 0),
            "destination": "Synthetic CRM prediction-score extension",
            "model_ref": result.get("model_ref"),
        },
        "risk": "No external business-system writeback occurs unless this approval is granted.",
    })
    return {"writeback_approval": answer}


def _route_writeback(state: MLDepartmentState) -> str:
    return "sync" if state.get("writeback_approval", {}).get("approved") else "finish_without_sync"


def _sync(state: MLDepartmentState) -> dict:
    result = sync_predictions(state["run_id"])
    return {"writeback_result": result}


def _no_sync(state: MLDepartmentState) -> dict:
    with SessionLocal() as db:
        # Resolve by the stable model_ref; the integer primary key is internal.
        candidate = db.query(ModelRecord).filter_by(model_ref=state["model_result"]["model_ref"]).one_or_none()
        if candidate:
            candidate.status = "APPROVED_NOT_SYNCED"
            db.commit()
    return {"writeback_result": {"records_written": 0, "destination": "Not synchronized — human rejected writeback."}}


def _measure_impact(state: MLDepartmentState) -> dict:
    impact = calculate_business_impact(state["run_id"], state["objective"])
    return {"business_impact": impact}


def _learn(state: MLDepartmentState) -> dict:
    impact = state.get("business_impact", {})
    model_metrics = state.get("model_result", {}).get("metrics", {})
    note = (
        f"Run {state['run_id']} completed for {OBJECTIVES[state['objective']]['label']}. "
        f"Holdout ROC AUC={model_metrics.get('roc_auc', 0):.3f}; "
        f"business-impact indicators={json.dumps(impact, sort_keys=True)}. "
        "Next review: compare these rankings with observed sales/retention outcomes before changing policy."
    )
    with SessionLocal() as db:
        db.add(BusinessReview(run_id=state["run_id"], objective=state["objective"], impact=impact, learning_note=note))
        db.commit()
    return {"learning_note": note}


def _finish(state: MLDepartmentState) -> dict:
    result = {
        "run_id": state["run_id"],
        "objective": state["objective"],
        "objective_label": OBJECTIVES[state["objective"]]["label"],
        "business_impact": state.get("business_impact", {}),
        "writeback": state.get("writeback_result", {}),
        "learning_note": state.get("learning_note", ""),
        "agent_trace": state.get("agent_trace", []),
        "task_plan": state.get("task_plan", {}),
        "review_result": state.get("review_result", {}),
        "human_approvals": {
            "business_question": state.get("question_approval", {}).get("approved", False),
            "model_promotion": state.get("model_approval", {}).get("approved", False),
            "business_system_writeback": state.get("writeback_approval", {}).get("approved", False),
        },
    }
    return {"workflow_result": result}


def _stop(state: MLDepartmentState) -> dict:
    return {"workflow_result": {
        "run_id": state["run_id"], "objective": state["objective"],
        "stopped_by_human": True,
        "message": "The workflow stopped at a human approval gate. No later stage was executed.",
        "question_approval": state.get("question_approval"),
        "model_approval": state.get("model_approval"),
        "writeback_approval": state.get("writeback_approval"),
    }}


def build_graph():
    graph = StateGraph(MLDepartmentState)
    graph.add_node("discover_sources", _discover)
    graph.add_node("profile_data", _profile)
    graph.add_node("plan_ml_tasks", _plan_tasks)
    graph.add_node("select_allowed_tools", _select_tools)
    graph.add_node("propose_business_questions", _propose_questions)
    graph.add_node("approve_business_question", _question_gate)
    graph.add_node("train_candidate_models", _train)
    graph.add_node("approve_model_promotion", _model_gate)
    graph.add_node("promote_model", _promote_model)
    graph.add_node("approve_business_writeback", _writeback_gate)
    graph.add_node("sync_predictions", _sync)
    graph.add_node("skip_writeback", _no_sync)
    graph.add_node("measure_business_impact", _measure_impact)
    graph.add_node("record_learning", _learn)
    graph.add_node("finish", _finish)
    graph.add_node("stop", _stop)

    graph.add_edge(START, "discover_sources")
    graph.add_edge("discover_sources", "profile_data")
    graph.add_edge("profile_data", "plan_ml_tasks")
    graph.add_edge("plan_ml_tasks", "select_allowed_tools")
    graph.add_edge("select_allowed_tools", "propose_business_questions")
    graph.add_edge("propose_business_questions", "approve_business_question")
    graph.add_conditional_edges("approve_business_question", _route_question,
                                {"train": "train_candidate_models", "stop": "stop"})
    graph.add_edge("train_candidate_models", "approve_model_promotion")
    graph.add_conditional_edges("approve_model_promotion", _route_model,
                                {"promote": "promote_model", "stop": "stop"})
    graph.add_edge("promote_model", "approve_business_writeback")
    graph.add_conditional_edges("approve_business_writeback", _route_writeback,
                                {"sync": "sync_predictions", "finish_without_sync": "skip_writeback"})
    graph.add_edge("sync_predictions", "measure_business_impact")
    graph.add_edge("skip_writeback", "finish")
    graph.add_edge("measure_business_impact", "record_learning")
    graph.add_edge("record_learning", "finish")
    graph.add_edge("finish", END)
    graph.add_edge("stop", END)
    return graph.compile(checkpointer=_checkpointer)


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def run_graph_start(initial_state: dict) -> dict:
    graph = get_graph()
    config = {"configurable": {"thread_id": initial_state["run_id"]}}
    return graph.invoke(initial_state, config=config)


def run_graph_resume(run_id: str, decision: dict) -> dict:
    graph = get_graph()
    config = {"configurable": {"thread_id": run_id}}
    return graph.invoke(Command(resume=decision), config=config)
