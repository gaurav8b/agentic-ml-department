"""FastAPI control plane and synthetic business-system endpoints."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
import json
import uuid

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session

from .config import settings
from .connectors import business_system_summary, systems_status
from .db import SessionLocal, engine, get_db
from .modeling import OBJECTIVES
from .models import Base, BusinessReview, Campaign, Customer, Lead, ModelRecord, OutcomeFeedback, Prediction, SalesOrder, SupervisorInstruction, SupportTicket, WorkflowRecord
from .seed import COMPANY_NAME, seed_demo_data
from .workflow import run_graph_resume, run_graph_start
from .tool_registry import build_default_registry

app = FastAPI(
    title="Agentic ML Department API",
    version="0.1.0",
    description="A human-supervised machine-learning department for a fully synthetic business.",
)


class StartRunRequest(BaseModel):
    objective: Literal["customer_churn", "lead_conversion"]
    supervisor_instructions: str = Field(default="", max_length=3000)


class ApprovalRequest(BaseModel):
    approved: bool
    comments: str = Field(default="", max_length=2000)
    selected_items: list[str] = Field(default_factory=list)


class OutcomeFeedbackRequest(BaseModel):
    objective: Literal["customer_churn", "lead_conversion"]
    entity_ref: str = Field(min_length=3, max_length=32)
    actual_outcome: bool
    source_run_id: str | None = None
    note: str = Field(default="", max_length=1000)


class InstructionRequest(BaseModel):
    instruction: str = Field(min_length=3, max_length=3000)


def _json_safe(value):
    return json.loads(json.dumps(value, default=str))


def _pack_run(row: WorkflowRecord) -> dict:
    return {
        "run_id": row.id, "objective": row.objective, "status": row.status,
        "stage": row.stage, "supervisor_instructions": row.supervisor_instructions,
        "state": row.state_json or {}, "pending_approval": row.pending_approval,
        "final_summary": row.final_summary,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _persist_graph_result(run_id: str, result: dict) -> dict:
    state = {k: v for k, v in result.items() if k != "__interrupt__"}
    interruptions = result.get("__interrupt__", ())
    pending = None
    if interruptions:
        pending = interruptions[0].value if hasattr(interruptions[0], "value") else str(interruptions[0])
    state = _json_safe(state)
    with SessionLocal() as db:
        row = db.get(WorkflowRecord, run_id)
        if row is None:
            raise RuntimeError(f"Workflow record {run_id} disappeared")
        row.state_json = state
        row.pending_approval = _json_safe(pending) if pending is not None else None
        row.updated_at = datetime.now(timezone.utc)
        if pending is not None:
            row.status = "AWAITING_APPROVAL"
            row.stage = pending.get("approval_type", "approval")
        elif state.get("workflow_result", {}).get("stopped_by_human"):
            row.status = "STOPPED_BY_HUMAN"
            row.stage = "stopped"
            row.final_summary = _json_safe(state.get("workflow_result"))
        elif state.get("workflow_result"):
            row.status = "COMPLETED"
            row.stage = "completed"
            row.final_summary = _json_safe(state.get("workflow_result"))
        else:
            row.status = "RUNNING"
            row.stage = "processing"
        db.commit()
        db.refresh(row)
        return _pack_run(row)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    if settings.auto_seed_demo:
        seed_demo_data(force=False)


@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.query(Customer).limit(1).all()
        return {"status": "ok", "company": COMPANY_NAME, "database": "connected"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}")


@app.get("/")
def root():
    return {"name": "Agentic ML Department", "docs": "/docs", "company": COMPANY_NAME,
            "objectives": OBJECTIVES, "dashboard": "http://localhost:8501"}


@app.get("/api/systems")
def get_systems():
    return {"company": COMPANY_NAME, "systems": systems_status()}


@app.get("/api/profiles")
def get_profiles():
    return business_system_summary()


@app.get("/api/agent-team")
def get_agent_team():
    """Describe the specialist agents and allow-listed tools in the demo."""
    return {
        "agents": [
            {"name": "data_perception_agent", "purpose": "Profile source tables and flag data-quality concerns."},
            {"name": "task_descriptor_agent", "purpose": "Translate the approved objective into a bounded, auditable task plan."},
            {"name": "tool_selector_agent", "purpose": "Select tools from the explicit Python allow-list."},
            {"name": "business_question_agent", "purpose": "Propose testable questions and business rationale."},
            {"name": "ml_execution_agent", "purpose": "Train approved fixed baseline pipelines and score the current cohort."},
            {"name": "model_review_agent", "purpose": "Check evaluation evidence before human model-promotion approval."},
            {"name": "business_integration_agent", "purpose": "Prepare the writeback preview; the supervisor decides whether to authorize it."},
            {"name": "business_feedback_agent", "purpose": "Record verified outcomes and create learning notes for later runs."},
        ],
        "tools": build_default_registry().describe(),
        "execution_policy": "No arbitrary generated Python or shell is executed. Business writeback is a separate human-approved action.",
    }


@app.post("/api/demo/seed")
def seed_demo(force: bool = Query(default=False)):
    return seed_demo_data(force=force)


@app.post("/api/runs")
def start_run(payload: StartRunRequest):
    run_id = str(uuid.uuid4())
    instructions = payload.supervisor_instructions.strip()
    with SessionLocal() as db:
        db.add(WorkflowRecord(
            id=run_id, objective=payload.objective, status="RUNNING", stage="discover_sources",
            supervisor_instructions=instructions, state_json={},
        ))
        if instructions:
            db.add(SupervisorInstruction(instruction=instructions, active=True))
        db.commit()
    initial_state = {
        "run_id": run_id, "objective": payload.objective,
        "supervisor_instructions": instructions,
    }
    try:
        result = run_graph_start(initial_state)
        return _persist_graph_result(run_id, result)
    except Exception as exc:
        with SessionLocal() as db:
            row = db.get(WorkflowRecord, run_id)
            if row:
                row.status = "FAILED"
                row.stage = "error"
                row.state_json = {"error": f"{type(exc).__name__}: {exc}"}
                db.commit()
        raise HTTPException(status_code=500, detail=f"Workflow failed: {type(exc).__name__}: {exc}") from exc


@app.get("/api/runs")
def list_runs(limit: int = Query(default=20, ge=1, le=100), db: Session = Depends(get_db)):
    rows = db.query(WorkflowRecord).order_by(desc(WorkflowRecord.created_at)).limit(limit).all()
    return [_pack_run(row) for row in rows]


@app.get("/api/runs/{run_id}")
def get_run(run_id: str, db: Session = Depends(get_db)):
    row = db.get(WorkflowRecord, run_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Workflow run not found")
    return _pack_run(row)


@app.post("/api/runs/{run_id}/resume")
def resume_run(run_id: str, payload: ApprovalRequest):
    with SessionLocal() as db:
        row = db.get(WorkflowRecord, run_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Workflow run not found")
        if row.status != "AWAITING_APPROVAL":
            raise HTTPException(status_code=409, detail=f"Run is not awaiting approval (status={row.status})")
        approval_type = (row.pending_approval or {}).get("approval_type", "unknown")
    decision = {
        "approved": payload.approved,
        "comments": payload.comments.strip(),
        "selected_items": payload.selected_items,
        "approval_type": approval_type,
        "decided_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        result = run_graph_resume(run_id, decision)
        return _persist_graph_result(run_id, result)
    except Exception as exc:
        with SessionLocal() as db:
            row = db.get(WorkflowRecord, run_id)
            if row:
                row.status = "FAILED"
                row.stage = "error"
                row.state_json = {"error": f"{type(exc).__name__}: {exc}"}
                db.commit()
        raise HTTPException(status_code=500, detail=f"Workflow resume failed: {type(exc).__name__}: {exc}") from exc


@app.post("/api/supervisor-instructions")
def add_instruction(payload: InstructionRequest, db: Session = Depends(get_db)):
    row = SupervisorInstruction(instruction=payload.instruction.strip(), active=True)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "instruction": row.instruction, "active": row.active,
            "created_at": row.created_at.isoformat()}


@app.get("/api/supervisor-instructions")
def list_instructions(db: Session = Depends(get_db)):
    rows = db.query(SupervisorInstruction).filter_by(active=True).order_by(desc(SupervisorInstruction.created_at)).limit(50).all()
    return [{"id": x.id, "instruction": x.instruction, "created_at": x.created_at.isoformat()} for x in rows]


@app.get("/api/models")
def list_models(db: Session = Depends(get_db)):
    rows = db.query(ModelRecord).order_by(desc(ModelRecord.created_at)).limit(50).all()
    return [{"model_ref": x.model_ref, "objective": x.objective, "version": x.version,
             "model_name": x.model_name, "status": x.status, "metrics": x.metrics,
             "created_at": x.created_at.isoformat()} for x in rows]


@app.get("/api/predictions")
def list_predictions(run_id: str | None = None, limit: int = Query(default=100, ge=1, le=1000), db: Session = Depends(get_db)):
    query = db.query(Prediction)
    if run_id:
        query = query.filter_by(run_id=run_id)
    rows = query.order_by(desc(Prediction.probability)).limit(limit).all()
    return [{"run_id": x.run_id, "objective": x.objective, "entity_ref": x.entity_ref,
             "probability": x.probability, "decision_threshold": x.decision_threshold,
             "recommendation": x.recommendation, "status": x.status,
             "created_at": x.created_at.isoformat()} for x in rows]


@app.get("/api/business-reviews")
def business_reviews(limit: int = Query(default=20, ge=1, le=100), db: Session = Depends(get_db)):
    rows = db.query(BusinessReview).order_by(desc(BusinessReview.created_at)).limit(limit).all()
    return [{"run_id": x.run_id, "objective": x.objective, "impact": x.impact,
             "learning_note": x.learning_note, "created_at": x.created_at.isoformat()} for x in rows]


@app.post("/api/outcomes")
def record_outcome(payload: OutcomeFeedbackRequest, db: Session = Depends(get_db)):
    """Record a human-confirmed outcome and update the synthetic labelled source row.

    The next approved training run will be able to learn from this corrected label.
    """
    prediction_query = db.query(Prediction).filter_by(
        objective=payload.objective, entity_ref=payload.entity_ref, status="SYNCED"
    )
    if payload.source_run_id:
        prediction_query = prediction_query.filter_by(run_id=payload.source_run_id)
    prediction = prediction_query.order_by(desc(Prediction.created_at)).first()
    if prediction is None:
        raise HTTPException(
            status_code=409,
            detail="Only a prediction previously synchronized after human approval can receive outcome feedback.",
        )
    if payload.objective == "customer_churn":
        entity = db.query(Customer).filter_by(customer_ref=payload.entity_ref).one_or_none()
        if entity is None:
            raise HTTPException(status_code=404, detail="Customer reference not found")
        entity.churned = payload.actual_outcome
        entity.is_current = False  # a verified horizon outcome turns a scored row into labelled history
    else:
        entity = db.query(Lead).filter_by(lead_ref=payload.entity_ref).one_or_none()
        if entity is None:
            raise HTTPException(status_code=404, detail="Lead reference not found")
        entity.converted = payload.actual_outcome
        entity.is_open = False  # a verified lead outcome is now a labelled historical example
    feedback = OutcomeFeedback(
        objective=payload.objective, entity_ref=payload.entity_ref,
        actual_outcome=payload.actual_outcome, source_run_id=prediction.run_id,
        note=payload.note.strip(),
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return {"recorded": True, "feedback_id": feedback.id, "objective": payload.objective,
            "entity_ref": payload.entity_ref, "actual_outcome": payload.actual_outcome,
            "message": "The source label was updated. A future model run can use this feedback."}


@app.get("/api/monitoring")
def monitoring(db: Session = Depends(get_db)):
    feedback_rows = db.query(OutcomeFeedback).order_by(desc(OutcomeFeedback.observed_at)).limit(5000).all()
    metrics_by_objective = {}
    for objective in OBJECTIVES:
        labels = {}
        for feedback in feedback_rows:  # rows are newest first; preserve the latest verified outcome per entity
            if feedback.objective == objective:
                labels.setdefault(feedback.entity_ref, bool(feedback.actual_outcome))
        scored = db.query(Prediction).filter_by(objective=objective, status="SYNCED").order_by(
            desc(Prediction.created_at)
        ).all()
        latest_by_entity = {}
        for row in scored:  # newest first; retain only the latest score for each entity
            latest_by_entity.setdefault(row.entity_ref, row)
        matched = [row for ref, row in latest_by_entity.items() if ref in labels]
        if matched:
            correct = sum((row.probability >= row.decision_threshold) == labels[row.entity_ref] for row in matched)
            brier = sum((row.probability - float(labels[row.entity_ref])) ** 2 for row in matched) / len(matched)
            metrics_by_objective[objective] = {"feedback_records": len(labels), "matched_predictions": len(matched),
                                               "threshold_accuracy": round(correct / len(matched), 4),
                                               "brier_score": round(brier, 4)}
        else:
            metrics_by_objective[objective] = {"feedback_records": len(labels), "matched_predictions": 0,
                                               "message": "No matching observed outcomes yet. Record outcomes using POST /api/outcomes."}
    return {"objectives": metrics_by_objective,
            "principle": "Observed outcomes are stored as labelled feedback. They inform future approved training runs; the system does not silently alter production policy."}


# Synthetic system endpoints: these mimic read-only business application APIs.
@app.get("/business/crm/customers")
def crm_customers(limit: int = Query(default=100, ge=1, le=1000), db: Session = Depends(get_db)):
    rows = db.query(Customer).limit(limit).all()
    return [{"customer_ref": x.customer_ref, "region": x.region, "segment": x.segment,
             "plan_type": x.plan_type, "monthly_spend": x.monthly_spend, "churned": x.churned} for x in rows]


@app.get("/business/crm/leads")
def crm_leads(limit: int = Query(default=100, ge=1, le=1000), db: Session = Depends(get_db)):
    rows = db.query(Lead).limit(limit).all()
    return [{"lead_ref": x.lead_ref, "lead_source": x.lead_source, "industry": x.industry,
             "budget_usd": x.budget_usd, "estimated_deal_value": x.estimated_deal_value,
             "converted": x.converted} for x in rows]


@app.get("/business/crm/prediction-scores")
def crm_prediction_scores(limit: int = Query(default=100, ge=1, le=1000), db: Session = Depends(get_db)):
    rows = db.query(Prediction).filter_by(status="SYNCED").order_by(desc(Prediction.probability)).limit(limit).all()
    return [{"entity_ref": x.entity_ref, "objective": x.objective, "probability": x.probability,
             "recommendation": x.recommendation, "synced_at": x.synced_at.isoformat() if x.synced_at else None} for x in rows]


@app.get("/business/lead-generation/leads")
def lead_generation_leads(limit: int = Query(default=100, ge=1, le=1000), db: Session = Depends(get_db)):
    rows = db.query(Lead).limit(limit).all()
    return [{"lead_ref": x.lead_ref, "lead_source": x.lead_source, "industry": x.industry,
             "company_size": x.company_size, "budget_usd": x.budget_usd,
             "website_visits_30d": x.website_visits_30d, "email_engagement": x.email_engagement,
             "sales_touchpoints": x.sales_touchpoints, "is_open": x.is_open} for x in rows]


@app.get("/business/erp/orders")
def erp_orders(limit: int = Query(default=100, ge=1, le=1000), db: Session = Depends(get_db)):
    rows = db.query(SalesOrder).order_by(desc(SalesOrder.order_date)).limit(limit).all()
    return [{"order_ref": x.order_ref, "customer_ref": x.customer_ref, "order_date": x.order_date.isoformat(),
             "category": x.category, "order_value": x.order_value, "discount_pct": x.discount_pct,
             "status": x.status} for x in rows]


@app.get("/business/marketing/campaigns")
def marketing_campaigns(limit: int = Query(default=100, ge=1, le=1000), db: Session = Depends(get_db)):
    rows = db.query(Campaign).limit(limit).all()
    return [{"campaign_ref": x.campaign_ref, "channel": x.channel, "objective": x.objective,
             "spend_usd": x.spend_usd, "leads_generated": x.leads_generated} for x in rows]


@app.get("/business/support/tickets")
def support_tickets(limit: int = Query(default=100, ge=1, le=1000), db: Session = Depends(get_db)):
    rows = db.query(SupportTicket).limit(limit).all()
    return [{"ticket_ref": x.ticket_ref, "customer_ref": x.customer_ref, "category": x.category,
             "priority": x.priority, "resolved_hours": x.resolved_hours,
             "satisfaction_after": x.satisfaction_after} for x in rows]
