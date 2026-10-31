from __future__ import annotations

import pytest

from agentic_ml_department.db import engine, SessionLocal
from agentic_ml_department.models import Base, Customer, Lead, ModelRecord, OutcomeFeedback, Prediction
from agentic_ml_department.seed import seed_demo_data
from agentic_ml_department.connectors import business_system_summary
from agentic_ml_department.modeling import train_and_score, load_objective_frame, calculate_business_impact


@pytest.fixture(scope="module", autouse=True)
def seeded_database():
    Base.metadata.create_all(bind=engine)
    seed_demo_data(force=True)
    yield


def test_synthetic_company_has_five_sources_and_expected_volume():
    snapshot = business_system_summary()
    assert snapshot["totals"]["tables"] == 5
    assert snapshot["totals"]["rows"] == 4452
    assert {x["system"] for x in snapshot["systems"]} == {
        "CRM", "Lead Generation", "ERP / Commerce", "Customer Support", "Marketing Automation"
    }
    assert all(x["status"] == "connected" for x in snapshot["systems"])
    customer_profile = next(x for x in snapshot["profiles"] if x["source"] == "CRM — customers")
    monthly_spend = next(x for x in customer_profile["fields"] if x["name"] == "monthly_spend")
    assert monthly_spend["summary"]["kind"] == "numeric"
    assert monthly_spend["summary"]["mean"] is not None
    assert isinstance(customer_profile["top_numeric_correlations"], list)
    assert "does not establish causation" in customer_profile["correlation_note"]


def test_churn_model_respects_supervisor_controls():
    result = train_and_score(
        "customer_churn", "pytest-churn-run", "Prioritize recall. Do not use satisfaction_score."
    )
    controls = result["supervisor_controls_applied"]
    assert controls["threshold"] == 0.35
    assert "satisfaction_score" in controls["excluded_features"]
    assert result["predictions_queued"] == 200
    assert result["metrics"]["rows_available"] == 500
    assert result["metrics"]["rows_scored"] == 200
    assert 0.0 <= result["metrics"]["roc_auc"] <= 1.0
    assert result["metrics"]["rows_evaluated"] > 0


def test_lead_conversion_model_respects_precision_instruction():
    result = train_and_score("lead_conversion", "pytest-leads-run", "Prioritize precision.")
    assert result["supervisor_controls_applied"]["threshold"] == 0.65
    assert result["predictions_queued"] == 250
    assert result["metrics"]["rows_available"] == 650
    assert result["metrics"]["rows_scored"] == 250
    with SessionLocal() as db:
        scored_refs = {x.entity_ref for x in db.query(Prediction).filter_by(run_id="pytest-leads-run").all()}
        current_refs = {x.lead_ref for x in db.query(Lead).filter_by(is_open=True).all()}
        historical_refs = {x.lead_ref for x in db.query(Lead).filter_by(is_open=False).all()}
        assert scored_refs <= current_refs
        assert scored_refs.isdisjoint(historical_refs)


def test_prediction_and_model_records_are_saved():
    with SessionLocal() as db:
        assert db.query(ModelRecord).filter_by(run_id="pytest-churn-run").count() == 1
        churn_predictions = db.query(Prediction).filter_by(run_id="pytest-churn-run").all()
    assert len(churn_predictions) == 200
    current_refs = {x.customer_ref for x in db.query(Customer).filter_by(is_current=True).all()}
    historical_refs = {x.customer_ref for x in db.query(Customer).filter_by(is_current=False).all()}
    scored_refs = {x.entity_ref for x in churn_predictions}
    assert scored_refs <= current_refs
    assert scored_refs.isdisjoint(historical_refs)


def test_verified_feedback_moves_a_scored_customer_into_future_training_history():
    with SessionLocal() as db:
        current_customer = db.query(Customer).filter_by(is_current=True).first()
        ref = current_customer.customer_ref
        current_customer.churned = False
        current_customer.is_current = False
        db.add(OutcomeFeedback(objective="customer_churn", entity_ref=ref, actual_outcome=False,
                               source_run_id="pytest-churn-run", note="Verified test outcome"))
        db.commit()
    result = train_and_score("customer_churn", "pytest-churn-retrain", "")
    assert result["metrics"]["rows_available"] == 501
    assert result["metrics"]["rows_scored"] == 199


def test_unsupported_objective_is_rejected():
    with pytest.raises(ValueError, match="Unknown objective"):
        load_objective_frame("employee_performance_risk")


def test_business_impact_uses_the_supervisor_approved_prediction_threshold():
    with SessionLocal() as db:
        customer = db.query(Customer).filter_by(is_current=True).first()
        db.add(Prediction(
            run_id="pytest-threshold-impact", objective="customer_churn",
            entity_ref=customer.customer_ref, probability=0.40, decision_threshold=0.35,
            recommendation="Review customer", status="SYNCED",
        ))
        db.commit()
        expected_monthly_spend = float(customer.monthly_spend)

    impact = calculate_business_impact("pytest-threshold-impact", "customer_churn")
    assert impact["high_risk_customers"] == 1
    assert impact["estimated_monthly_revenue_at_risk_usd"] == round(expected_monthly_spend, 2)
