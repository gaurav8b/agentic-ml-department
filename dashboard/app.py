"""Beginner-friendly supervisory console for the synthetic ML department."""
from __future__ import annotations

import os
import requests
import streamlit as st

API = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="Northstar | AI ML Department", page_icon="🧭", layout="wide")
st.title("🧭 Northstar Office & Cloud")
st.subheader("Agentic Machine-Learning Department — supervised demo")
st.caption("A fictional business. All records and financial values are synthetic. The system proposes, experiments and prepares actions; a person approves the business question, model promotion and writeback.")


def api(method: str, path: str, **kwargs):
    try:
        response = requests.request(method, f"{API}{path}", timeout=120, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        st.error(f"Cannot reach the project API at {API}. Start the project using the README instructions. Details: {exc}")
        return None


health = api("GET", "/health")
if health:
    st.success(f"Database connected · {health.get('company')} · API ready")

systems = api("GET", "/api/systems")
profiles = api("GET", "/api/profiles")
if systems:
    cols = st.columns(len(systems["systems"]))
    for col, system in zip(cols, systems["systems"]):
        col.metric(system["system"], f"{system['records']:,} records", system["status"].upper())

st.divider()
left, right = st.columns([1.15, 0.85])
with left:
    st.header("1. Start a business question")
    objective = st.selectbox(
        "What should the ML department investigate?",
        options=["customer_churn", "lead_conversion"],
        format_func=lambda x: "Customer churn risk — identify customers who may leave" if x == "customer_churn" else "Lead conversion — prioritize prospects most likely to buy",
    )
    instruction = st.text_area(
        "Supervisory instructions (optional)",
        placeholder="Example: Prioritize recall. Do not use satisfaction_score. Explain the trade-off before promoting the model.",
        help="Supported demonstration controls: 'prioritize recall' lowers the alert threshold; 'prioritize precision' raises it; 'do not use FIELD_NAME' excludes a known feature. Other instructions are retained and shown to the optional local language model, but are not silently executed as policy.",
    )
    if st.button("Start supervised ML workflow", type="primary", use_container_width=True):
        with st.spinner("Discovering source systems, profiling data and preparing the business question…"):
            run = api("POST", "/api/runs", json={"objective": objective, "supervisor_instructions": instruction})
        if run:
            st.session_state["active_run_id"] = run["run_id"]
            st.rerun()

with right:
    st.header("2. What is connected?")
    if profiles:
        st.metric("Total records", f"{profiles['totals']['rows']:,}")
        for p in profiles["profiles"]:
            with st.expander(f"{p['source']} · {p['rows']:,} rows"):
                st.write(f"Columns: {p['columns']} · Missing values: {p['missing_cells']} · Duplicate rows: {p['duplicate_rows']}")
                st.caption("Field summaries show numeric distributions or the most common categories. Samples are illustrative.")
                st.dataframe(p["fields"], use_container_width=True, hide_index=True)
                if p.get("top_numeric_correlations"):
                    st.write("Strongest numeric associations (not evidence of causation)")
                    st.dataframe(p["top_numeric_correlations"], use_container_width=True, hide_index=True)

st.divider()
st.header("3. Approval inbox")
runs = api("GET", "/api/runs?limit=30") or []
pending_runs = [r for r in runs if r["status"] == "AWAITING_APPROVAL"]
if not pending_runs:
    st.info("No approvals are waiting. Start a workflow above to see the agent team ask for approval at each controlled stage.")
else:
    labels = {f"{r['run_id'][:8]} · {r['stage']} · {r['objective']}": r for r in pending_runs}
    selected = st.selectbox("Choose a run awaiting your decision", list(labels.keys()))
    run = labels[selected]
    approval = run.get("pending_approval") or {}
    st.subheader(approval.get("title", "Approval required"))
    st.write(approval.get("instruction", "Review and decide."))
    kind = approval.get("approval_type")
    if kind == "business_question":
        proposal = approval.get("proposal", {})
        st.write(f"**Business objective:** {proposal.get('objective_label', run['objective'])}")
        st.write(proposal.get("data_note", ""))
        if proposal.get("task_plan"):
            with st.expander("Agent-generated execution plan", expanded=True):
                st.write(proposal["task_plan"].get("business_value", ""))
                st.dataframe(proposal["task_plan"].get("steps", []), use_container_width=True, hide_index=True)
        if proposal.get("selected_tools"):
            with st.expander("Allow-listed tools selected for this workflow"):
                st.dataframe(proposal["selected_tools"], use_container_width=True, hide_index=True)
        for q in proposal.get("questions", []):
            st.markdown(f"**{q['question']}**\n\n{q['business_reason']}")
        if proposal.get("llm_advice"):
            st.info(f"Optional language-model advice: {proposal['llm_advice']}")
    elif kind == "model_promotion":
        candidate = approval.get("candidate", {})
        metrics = candidate.get("metrics", {})
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("ROC AUC", f"{metrics.get('roc_auc', 0):.3f}")
        c2.metric("PR AUC", f"{metrics.get('pr_auc', 0):.3f}")
        c3.metric("Precision", f"{metrics.get('precision', 0):.3f}")
        c4.metric("Recall", f"{metrics.get('recall', 0):.3f}")
        gate = approval.get("quality_gate", {})
        (st.success if gate.get("passed") else st.warning)(gate.get("message", "Quality gate information unavailable."))
        st.write(f"Selected baseline: **{candidate.get('model_name')}** · Scored records queued: **{candidate.get('predictions_queued', 0):,}**")
        if candidate.get("supervisor_controls_applied"):
            st.json(candidate["supervisor_controls_applied"])
        st.caption(candidate.get("evaluation_note", ""))
        if approval.get("automated_review"):
            st.write("Independent automated reviewer")
            st.json(approval["automated_review"])
        if candidate.get("feature_importance"):
            st.write("Most influential model inputs (association, not proof of causation)")
            st.dataframe(candidate["feature_importance"], use_container_width=True, hide_index=True)
        if not gate.get("passed"):
            st.warning("A model below the demo quality bar requires a documented override reason to proceed.")
    elif kind == "business_system_writeback":
        st.warning(approval.get("risk", ""))
        st.json(approval.get("preview", {}))
    st.markdown(f"**Control:** {approval.get('risk', 'Review carefully before proceeding.')}")
    if kind == "business_question":
        st.caption("Add context or run-specific instructions here. Comments are retained with this decision and passed into the model-training instruction context; this prototype still runs the selected objective shown above.")
        comments_label = "Your response / additional run instructions"
    else:
        st.caption("Your comments are stored with this approval decision. Any condition that must change system behavior needs an explicitly implemented and tested rule.")
        comments_label = "Approval comments / reason"
    comments = st.text_area(comments_label, key=f"comments-{run['run_id']}-{kind}")
    a1, a2 = st.columns(2)
    if a1.button("Approve and continue", type="primary", use_container_width=True, key=f"yes-{run['run_id']}-{kind}"):
        with st.spinner("Resuming the workflow…"):
            updated = api("POST", f"/api/runs/{run['run_id']}/resume", json={"approved": True, "comments": comments})
        if updated:
            st.success(f"Decision recorded. Current status: {updated['status']} · {updated['stage']}")
            st.rerun()
    if a2.button("Reject / stop", use_container_width=True, key=f"no-{run['run_id']}-{kind}"):
        updated = api("POST", f"/api/runs/{run['run_id']}/resume", json={"approved": False, "comments": comments})
        if updated:
            st.warning("Workflow stopped at this gate.")
            st.rerun()

st.divider()
st.header("4. Agent activity and run history")
if runs:
    selected_completed = st.selectbox("Inspect run details", [r["run_id"] for r in runs], format_func=lambda x: x[:8])
    details = api("GET", f"/api/runs/{selected_completed}")
    if details:
        trace = details.get("state", {}).get("agent_trace", [])
        if trace:
            st.write("Specialist-agent execution trace")
            st.dataframe(trace, use_container_width=True, hide_index=True)
        task_plan = details.get("state", {}).get("task_plan")
        if task_plan:
            with st.expander("Task plan"):
                st.json(task_plan)
if runs:
    st.dataframe([{"run": r["run_id"][:8], "objective": r["objective"], "status": r["status"], "stage": r["stage"], "created": r["created_at"]} for r in runs], use_container_width=True, hide_index=True)
reviews = api("GET", "/api/business-reviews?limit=10") or []
for review in reviews:
    with st.expander(f"Business review · {review['objective']} · run {review['run_id'][:8]}"):
        st.json(review["impact"])
        st.write(review["learning_note"])

st.subheader("6. Record a verified outcome")
st.caption("This is how a future training run can learn from a corrected label. Only record an outcome that has actually been checked.")
predictions = api("GET", "/api/predictions?limit=1000") or []
synced_predictions = [p for p in predictions if p["status"] == "SYNCED"]
if synced_predictions:
    prediction_labels = {f"{p['entity_ref']} · {p['objective']} · score {p['probability']:.2f}": p for p in synced_predictions}
    chosen_label = st.selectbox("Select a synchronized prediction", list(prediction_labels.keys()))
    chosen_prediction = prediction_labels[chosen_label]
    actual = st.radio("What was the verified outcome?", options=[False, True], format_func=lambda x: "No — the predicted event did not happen" if not x else "Yes — the predicted event happened", horizontal=True)
    feedback_note = st.text_input("Evidence / reviewer note", placeholder="For example: verified from the updated CRM record")
    if st.button("Record verified outcome"):
        result = api("POST", "/api/outcomes", json={
            "objective": chosen_prediction["objective"],
            "entity_ref": chosen_prediction["entity_ref"],
            "actual_outcome": actual,
            "source_run_id": chosen_prediction["run_id"],
            "note": feedback_note,
        })
        if result:
            st.success(result["message"])
            st.rerun()
else:
    st.info("No synchronized predictions are available yet. Approve a model and the separate writeback request first.")

monitoring = api("GET", "/api/monitoring")
if monitoring:
    st.write("Observed outcomes matched to synchronized predictions")
    st.json(monitoring["objectives"])

st.caption("Prototype boundary: the demo uses generated records and simulated CRM/ERP/marketing/support APIs. A real deployment needs approved connectors, identity controls, secrets management, legal/privacy review, monitoring and an operational owner.")
