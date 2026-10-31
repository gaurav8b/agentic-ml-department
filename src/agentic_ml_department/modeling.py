"""Reproducible tabular ML: leakage-aware splits, baselines, metrics and predictions."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import re
import uuid
from pathlib import Path
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score, f1_score,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import settings
from .connectors import CRMConnector
from .db import SessionLocal
from .models import Customer, Lead, ModelRecord, Prediction

OBJECTIVES = {
    "customer_churn": {
        "label": "Customer churn risk",
        "business_question": "Which current customers are most likely to stop buying or leave, so the retention team can intervene earlier?",
        "target": "churned",
        "entity": "customer",
        "minimum_rows": 200,
        "business_value": "Prioritize retention conversations and estimate recurring revenue exposed to churn.",
    },
    "lead_conversion": {
        "label": "Lead conversion propensity",
        "business_question": "Which open leads are most likely to become customers, so sales can prioritize follow-up?",
        "target": "converted",
        "entity": "lead",
        "minimum_rows": 200,
        "business_value": "Rank the sales queue and focus outreach on high-propensity opportunities.",
    },
}

FEATURES = {
    "customer_churn": {
        "numeric": ["tenure_months", "monthly_spend", "days_since_last_purchase", "support_tickets_90d", "satisfaction_score"],
        "categorical": ["region", "segment", "acquisition_channel", "plan_type", "contract_type"],
    },
    "lead_conversion": {
        "numeric": ["company_size", "budget_usd", "website_visits_30d", "email_engagement", "sales_touchpoints"],
        "categorical": ["lead_source", "industry"],
    },
}


def load_objective_frame(objective: str) -> tuple[pd.DataFrame, list[str]]:
    if objective not in OBJECTIVES:
        raise ValueError(f"Unknown objective: {objective}")
    frame = CRMConnector().customers() if objective == "customer_churn" else CRMConnector().leads()
    feature_names = FEATURES[objective]["numeric"] + FEATURES[objective]["categorical"]
    target = OBJECTIVES[objective]["target"]
    missing = [col for col in feature_names + [target] if col not in frame.columns]
    if missing:
        raise ValueError(f"Required fields missing from source data: {missing}")
    return frame, feature_names


def _pipeline(objective: str, model_kind: str, feature_names: list[str]) -> Pipeline:
    numeric = [name for name in FEATURES[objective]["numeric"] if name in feature_names]
    categorical = [name for name in FEATURES[objective]["categorical"] if name in feature_names]
    numeric_pipe = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
    categorical_pipe = Pipeline([("imputer", SimpleImputer(strategy="most_frequent")),
                                 ("onehot", OneHotEncoder(handle_unknown="ignore"))])
    prep = ColumnTransformer([("numeric", numeric_pipe, numeric),
                              ("categorical", categorical_pipe, categorical)])
    if model_kind == "logistic_regression":
        estimator = LogisticRegression(max_iter=1200, class_weight="balanced", random_state=42)
    elif model_kind == "random_forest":
        estimator = RandomForestClassifier(n_estimators=220, min_samples_leaf=3,
                                           class_weight="balanced_subsample", random_state=42, n_jobs=-1)
    else:
        raise ValueError(f"Unsupported model kind: {model_kind}")
    return Pipeline([("preprocess", prep), ("model", estimator)])


def _metrics(y_true: pd.Series, probabilities: np.ndarray, predictions: np.ndarray, threshold: float) -> dict:
    values = {
        "accuracy": float(accuracy_score(y_true, predictions)),
        "precision": float(precision_score(y_true, predictions, zero_division=0)),
        "recall": float(recall_score(y_true, predictions, zero_division=0)),
        "f1": float(f1_score(y_true, predictions, zero_division=0)),
        "decision_threshold": float(threshold),
        "positive_rate_actual": float(np.mean(y_true)),
        "positive_rate_predicted": float(np.mean(predictions)),
    }
    values["roc_auc"] = float(roc_auc_score(y_true, probabilities)) if len(np.unique(y_true)) == 2 else 0.5
    values["pr_auc"] = float(average_precision_score(y_true, probabilities)) if len(np.unique(y_true)) == 2 else 0.0
    return values


def _feature_importance(model: Pipeline, sample: pd.DataFrame, objective: str) -> list[dict]:
    estimator = model.named_steps["model"]
    prep = model.named_steps["preprocess"]
    try:
        names = prep.get_feature_names_out()
        if hasattr(estimator, "feature_importances_"):
            values = estimator.feature_importances_
        elif hasattr(estimator, "coef_"):
            values = np.abs(estimator.coef_[0])
        else:
            return []
        pairs = sorted(zip(names, values), key=lambda x: float(x[1]), reverse=True)[:10]
        return [{"feature": str(name).replace("numeric__", "").replace("categorical__", ""),
                 "importance": float(value)} for name, value in pairs]
    except Exception as exc:  # Feature explanations must never prevent a usable model run.
        warnings.warn(f"Feature importance unavailable: {exc}")
        return []


def _log_mlflow(objective: str, run_id: str, model_name: str, metrics: dict, artifact_path: Path) -> str | None:
    if not settings.mlflow_tracking_uri:
        return None
    try:
        import mlflow
        mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        mlflow.set_experiment("Agentic ML Department — Synthetic Business")
        with mlflow.start_run(run_name=f"{objective}-{run_id[:8]}"):
            mlflow.log_param("objective", objective)
            mlflow.log_param("selected_model", model_name)
            mlflow.log_param("run_id", run_id)
            mlflow.log_metrics({k: v for k, v in metrics.items() if isinstance(v, (int, float))})
            mlflow.log_artifact(str(artifact_path))
            return mlflow.active_run().info.run_id
    except Exception as exc:
        # MLflow is observability, not a hard dependency for the core workflow.
        warnings.warn(f"MLflow logging skipped: {exc}")
        return None


def train_and_score(objective: str, run_id: str, supervisor_instructions: str = "") -> dict:
    """Train candidate baselines, select the strongest, score current records, persist a candidate.

    A holdout set is used for evaluation. The selected pipeline is then refit on all
    labelled historical rows and scores a separate current population. No external
    business system is updated here.
    """
    frame, feature_names = load_objective_frame(objective)
    spec = OBJECTIVES[objective]
    cohort_column = "is_current" if objective == "customer_churn" else "is_open"
    training_frame = frame.loc[~frame[cohort_column].astype(bool)].copy()
    scoring_frame = frame.loc[frame[cohort_column].astype(bool)].copy()
    if training_frame.empty or scoring_frame.empty:
        raise ValueError(f"The {objective} dataset needs both labelled historical records and a separate current scoring population.")
    instruction_lower = supervisor_instructions.lower()
    supported_controls = {"threshold": 0.50, "excluded_features": [], "notes": []}
    if re.search(r"prioriti[sz]e recall|higher recall|recall over precision", instruction_lower):
        supported_controls["threshold"] = 0.35
        supported_controls["notes"].append("Decision threshold lowered to 0.35 to favor recall; review precision before operational use.")
    elif re.search(r"prioriti[sz]e precision|higher precision|precision over recall", instruction_lower):
        supported_controls["threshold"] = 0.65
        supported_controls["notes"].append("Decision threshold raised to 0.65 to favor precision; review recall before operational use.")
    for candidate in list(feature_names):
        if re.search(rf"(?:exclude|omit|do not use|don't use|remove)\s+(?:the\s+)?{re.escape(candidate)}\b", instruction_lower):
            feature_names.remove(candidate)
            supported_controls["excluded_features"].append(candidate)
    if not feature_names:
        raise ValueError("Supervisor instructions excluded every available model feature.")
    if not supported_controls["notes"] and not supported_controls["excluded_features"] and supervisor_instructions.strip():
        supported_controls["notes"].append("Instruction recorded for supervisory context; no matching deterministic training control was detected. It was not silently treated as an executable policy.")
    target = spec["target"]
    if len(training_frame) < spec["minimum_rows"]:
        raise ValueError(f"At least {spec['minimum_rows']} labelled historical rows are required; found {len(training_frame)}")
    X = training_frame[feature_names].copy()
    y = training_frame[target].astype(int)
    if y.nunique() < 2:
        raise ValueError("The target contains only one class; a classifier cannot be evaluated.")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.22, random_state=42, stratify=y
    )

    candidate_results = []
    for model_kind in ("logistic_regression", "random_forest"):
        model = _pipeline(objective, model_kind, feature_names)
        model.fit(X_train, y_train)
        proba = model.predict_proba(X_test)[:, 1]
        pred = (proba >= supported_controls["threshold"]).astype(int)
        metrics = _metrics(y_test, proba, pred, supported_controls["threshold"])
        candidate_results.append((metrics["roc_auc"], model_kind, metrics))
    candidate_results.sort(key=lambda item: item[0], reverse=True)
    _, selected_kind, holdout_metrics = candidate_results[0]

    final_model = _pipeline(objective, selected_kind, feature_names)
    final_model.fit(X, y)
    current_probabilities = final_model.predict_proba(scoring_frame[feature_names])[:, 1]
    artifact_dir = settings.model_artifact_dir
    artifact_dir.mkdir(parents=True, exist_ok=True)
    model_path = artifact_dir / f"{objective}_{run_id}.joblib"
    joblib.dump(final_model, model_path)
    importance = _feature_importance(final_model, X_test, objective)

    predictions: list[Prediction] = []
    ids = scoring_frame["customer_ref" if objective == "customer_churn" else "lead_ref"].tolist()
    for entity_ref, prob in zip(ids, current_probabilities):
        p = float(prob)
        if objective == "customer_churn":
            advice = "Offer a retention check-in and review support history." if p >= supported_controls["threshold"] else "Continue normal lifecycle engagement."
        else:
            advice = "Prioritize a timely sales follow-up." if p >= supported_controls["threshold"] else "Keep in standard nurture; do not over-prioritize."
        predictions.append(Prediction(
            run_id=run_id, objective=objective, entity_ref=str(entity_ref), probability=p,
            decision_threshold=float(supported_controls["threshold"]),
            recommendation=advice, status="PENDING_APPROVAL",
        ))

    metrics = {
        **holdout_metrics,
        "rows_evaluated": int(len(y_test)),
        "rows_available": int(len(training_frame)),
        "rows_scored": int(len(scoring_frame)),
        "positive_examples": int(y.sum()),
        "positive_rate": float(y.mean()),
        "model_candidates": [{"name": name, **m} for _, name, m in candidate_results],
    }
    model_ref = str(uuid.uuid4())
    with SessionLocal() as db:
        version = db.query(ModelRecord).filter_by(objective=objective).count() + 1
        record = ModelRecord(
            model_ref=model_ref, run_id=run_id, objective=objective, version=version,
            model_name=selected_kind, artifact_path=str(model_path), metrics=metrics, status="CANDIDATE",
        )
        db.add(record)
        db.add_all(predictions)
        db.commit()

    mlflow_run_id = _log_mlflow(objective, run_id, selected_kind, holdout_metrics, model_path)
    return {
        "model_ref": model_ref,
        "objective": objective,
        "objective_label": spec["label"],
        "model_name": selected_kind,
        "artifact_path": str(model_path),
        "metrics": metrics,
        "feature_importance": importance,
        "predictions_queued": len(predictions),
        "mlflow_run_id": mlflow_run_id,
        "supervisor_instructions_recorded": bool(supervisor_instructions.strip()),
        "supervisor_controls_applied": supported_controls,
        "evaluation_note": "Metrics are measured on a stratified holdout set. The final scoring model is refit on all labelled historical rows and then scores a separate current population.",
    }


def activate_model(model_ref: str) -> None:
    with SessionLocal() as db:
        record = db.query(ModelRecord).filter_by(model_ref=model_ref).one()
        db.query(ModelRecord).filter_by(objective=record.objective, status="ACTIVE").update({"status": "SUPERSEDED"})
        record.status = "ACTIVE"
        db.commit()


def sync_predictions(run_id: str) -> dict:
    """Simulated CRM/lead-system writeback. Called only after its human approval gate."""
    with SessionLocal() as db:
        rows = db.query(Prediction).filter_by(run_id=run_id, status="PENDING_APPROVAL").all()
        now = datetime.now(timezone.utc)
        for row in rows:
            row.status = "SYNCED"
            row.synced_at = now
        db.commit()
        return {"records_written": len(rows), "destination": "Synthetic CRM prediction-score extension", "synced_at": now.isoformat()}


def calculate_business_impact(run_id: str, objective: str) -> dict:
    with SessionLocal() as db:
        rows = db.query(Prediction).filter_by(run_id=run_id, status="SYNCED").all()
        if objective == "customer_churn":
            by_ref = {c.customer_ref: c for c in db.query(Customer).all()}
            high = [p for p in rows if p.probability >= p.decision_threshold]
            at_risk_revenue = sum(by_ref[p.entity_ref].monthly_spend for p in high if p.entity_ref in by_ref)
            return {
                "objective": objective, "scored_customers": len(rows), "high_risk_customers": len(high),
                "estimated_monthly_revenue_at_risk_usd": round(float(at_risk_revenue), 2),
                "estimated_annual_revenue_at_risk_usd": round(float(at_risk_revenue * 12), 2),
                "interpretation": "Revenue-at-risk is a prioritization estimate, not a forecast of guaranteed losses or recoverable revenue.",
            }
        by_ref = {l.lead_ref: l for l in db.query(Lead).all()}
        high = [p for p in rows if p.probability >= p.decision_threshold]
        pipeline = sum(by_ref[p.entity_ref].estimated_deal_value for p in high if p.entity_ref in by_ref)
        return {
            "objective": objective, "scored_leads": len(rows), "high_propensity_leads": len(high),
            "estimated_pipeline_value_usd": round(float(pipeline), 2),
            "interpretation": "Pipeline value is an unweighted estimate attached to prioritized leads; it is not booked revenue.",
        }
