"""Business, workflow, prediction and model-registry tables."""
from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_ref: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    signup_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    region: Mapped[str] = mapped_column(String(40))
    segment: Mapped[str] = mapped_column(String(40))
    acquisition_channel: Mapped[str] = mapped_column(String(40))
    plan_type: Mapped[str] = mapped_column(String(40))
    contract_type: Mapped[str] = mapped_column(String(30))
    tenure_months: Mapped[int] = mapped_column(Integer)
    monthly_spend: Mapped[float] = mapped_column(Float)
    days_since_last_purchase: Mapped[int] = mapped_column(Integer)
    support_tickets_90d: Mapped[int] = mapped_column(Integer)
    satisfaction_score: Mapped[float] = mapped_column(Float)
    churned: Mapped[bool] = mapped_column(Boolean, index=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, index=True)


class Lead(Base):
    __tablename__ = "leads"
    id: Mapped[int] = mapped_column(primary_key=True)
    lead_ref: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    lead_source: Mapped[str] = mapped_column(String(40))
    industry: Mapped[str] = mapped_column(String(50))
    company_size: Mapped[int] = mapped_column(Integer)
    budget_usd: Mapped[float] = mapped_column(Float)
    website_visits_30d: Mapped[int] = mapped_column(Integer)
    email_engagement: Mapped[float] = mapped_column(Float)
    sales_touchpoints: Mapped[int] = mapped_column(Integer)
    converted: Mapped[bool] = mapped_column(Boolean, index=True)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    estimated_deal_value: Mapped[float] = mapped_column(Float)


class SalesOrder(Base):
    __tablename__ = "sales_orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_ref: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    customer_ref: Mapped[str] = mapped_column(String(32), index=True)
    order_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    category: Mapped[str] = mapped_column(String(40))
    order_value: Mapped[float] = mapped_column(Float)
    discount_pct: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(30))


class SupportTicket(Base):
    __tablename__ = "support_tickets"
    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_ref: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    customer_ref: Mapped[str] = mapped_column(String(32), index=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    category: Mapped[str] = mapped_column(String(40))
    priority: Mapped[str] = mapped_column(String(20))
    resolved_hours: Mapped[float] = mapped_column(Float)
    satisfaction_after: Mapped[float] = mapped_column(Float)


class Campaign(Base):
    __tablename__ = "marketing_campaigns"
    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_ref: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    channel: Mapped[str] = mapped_column(String(40))
    objective: Mapped[str] = mapped_column(String(60))
    spend_usd: Mapped[float] = mapped_column(Float)
    leads_generated: Mapped[int] = mapped_column(Integer)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Prediction(Base):
    __tablename__ = "prediction_scores"
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), index=True)
    objective: Mapped[str] = mapped_column(String(60), index=True)
    entity_ref: Mapped[str] = mapped_column(String(32), index=True)
    probability: Mapped[float] = mapped_column(Float)
    decision_threshold: Mapped[float] = mapped_column(Float, default=0.5)
    recommendation: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="PENDING_APPROVAL", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ModelRecord(Base):
    __tablename__ = "model_registry"
    id: Mapped[int] = mapped_column(primary_key=True)
    model_ref: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    run_id: Mapped[str] = mapped_column(String(36), index=True)
    objective: Mapped[str] = mapped_column(String(60), index=True)
    version: Mapped[int] = mapped_column(Integer)
    model_name: Mapped[str] = mapped_column(String(100))
    artifact_path: Mapped[str] = mapped_column(Text)
    metrics: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(30), default="CANDIDATE", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class WorkflowRecord(Base):
    __tablename__ = "workflow_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    objective: Mapped[str] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(40), index=True)
    stage: Mapped[str] = mapped_column(String(60), default="created")
    supervisor_instructions: Mapped[str] = mapped_column(Text, default="")
    state_json: Mapped[dict] = mapped_column(JSON, default=dict)
    pending_approval: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    final_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class SupervisorInstruction(Base):
    __tablename__ = "supervisor_instructions"
    id: Mapped[int] = mapped_column(primary_key=True)
    instruction: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class BusinessReview(Base):
    __tablename__ = "business_reviews"
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), index=True)
    objective: Mapped[str] = mapped_column(String(60))
    impact: Mapped[dict] = mapped_column(JSON)
    learning_note: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class OutcomeFeedback(Base):
    __tablename__ = "outcome_feedback"
    id: Mapped[int] = mapped_column(primary_key=True)
    objective: Mapped[str] = mapped_column(String(60), index=True)
    entity_ref: Mapped[str] = mapped_column(String(32), index=True)
    actual_outcome: Mapped[bool] = mapped_column(Boolean)
    source_run_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    note: Mapped[str] = mapped_column(Text, default="")
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
