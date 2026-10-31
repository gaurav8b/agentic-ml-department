# Machine-Learning Department — Step-by-Step Tutorial

This tutorial assumes you are an intelligent business user who has never built a data or AI project. You will use the running synthetic company and supervise a complete prediction workflow.

## Part 1 — understand the fictional company

Northstar Office & Cloud sells business equipment, subscriptions and related services. It has five simulated business systems:

1. **CRM:** existing customers, contracts, spending and sales leads.
2. **Lead generation:** prospect source, website activity, email engagement and sales contact history.
3. **ERP / commerce:** completed, returned and cancelled orders.
4. **Marketing automation:** channel, campaign objective, campaign spend and leads generated.
5. **Customer support:** ticket category, priority, resolution time and satisfaction after support.

The data generator creates 700 customers (500 historical, 200 current), 900 leads (650 closed historical, 250 open), 2,200 orders, 640 support tickets and 12 marketing campaigns. Historical labelled rows are used for model training; a separate current population is scored for action. This avoids evaluating a customer or lead using a model that has already seen that same labelled record. Values are fictitious and generated for repeatable testing. They do not describe a real company.

## Part 2 — understand the two initial prediction jobs

### Job A: customer churn risk

The model estimates which existing customers resemble customers who historically left. The customer-success team can review the highest scores and decide whether to contact them.

This is not a claim that the customer will definitely leave. A score is a prioritization signal, not a fact about an individual's future.

### Job B: lead conversion propensity

The model estimates which open leads resemble leads that historically converted. The sales team can use the ranking to plan follow-up.

A high score does not guarantee a sale and must not be used to ignore other leads or discriminate against protected groups.

## Part 3 — start the application

Follow the Docker steps in the main README. When all services are ready, open:

- Dashboard: http://localhost:8501
- API explorer: http://localhost:8000/docs
- MLflow: http://localhost:5000

The API and database are separate services. This is intentional: the UI does not need direct database credentials; it talks to the API.

## Part 4 — run the customer churn workflow

1. In the dashboard, select **Customer churn risk**.
2. In the supervisor-instructions box, enter: `Prioritize recall. Do not use satisfaction_score.`
3. Start the workflow.
4. Wait for the first approval card to appear.

At this stage the workflow has discovered the synthetic systems and profiled the datasets. It has proposed a business question and supporting analysis questions.

### First approval: business question

Check the wording. Ask yourself:

- Is this a question the business can act on?
- Does the source data contain relevant information?
- Does the team know what action it might take after seeing the score?

Approve to continue, or reject to stop. Your comments are recorded with the decision. This first decision is the permission to develop the requested model, not permission to change the CRM.

## Part 5 — inspect the model experiment

The workflow trains two baseline approaches:

- Logistic regression: a relatively simple model that estimates how inputs relate to the likelihood of the outcome.
- Random forest: a collection of decision trees combined to make a prediction.

The system compares them using a holdout dataset that was not used to fit the candidate model. It records:

- **ROC AUC:** how well the model ranks positive cases above negative cases across thresholds.
- **PR AUC:** a useful ranking summary when positive events are uncommon.
- **Precision:** how many flagged cases are truly positive.
- **Recall:** how many truly positive cases the model finds.
- **F1:** a combined measure of precision and recall.

The example instruction `Prioritize recall` lowers the decision threshold to 0.35. This usually catches more positive cases but can also create more false alarms. Excluding `satisfaction_score` removes that feature from both candidate model pipelines. These are simple, explicit prototype rules; they are not a general natural-language policy compiler.

### Second approval: model promotion

Review the metrics, the test sample size and the leading model inputs. Ask whether the model is useful enough for the proposed workflow. Approve or reject.

The minimum ROC AUC of 0.60 and minimum row count in this prototype are simple demonstration gates. They are not sufficient acceptance criteria for a real business. A real model must be assessed against business costs, data representativeness, fairness, leakage, temporal validity and operational capacity.

## Part 6 — approve or reject the business-system update

After model promotion, the system prepares a set of scores and a destination preview. It does not update the simulated CRM extension until you approve this separate request.

### Third approval: writeback

Review:

- Which prediction objective is being published.
- How many records are in the batch.
- Which model version produced them.
- Which synthetic business-system endpoint will receive the data.

Approve to mark the prediction records as synchronized. Reject to leave the scores un-synchronized. No real customer or external application is contacted.

## Part 7 — inspect business impact

After approved writeback, the system calculates an estimate:

- For churn, the count of high-risk customers and their approximate monthly/annual recurring spend exposure.
- For leads, the count of high-propensity prospects and the estimated deal value attached to them.

These are prioritization estimates. They are not guaranteed losses, savings, conversions or revenue.

The system writes a business-review note. It records the model result, the estimated business signal and what the owner should check next.

## Part 8 — close the learning loop with observed outcomes

A model improves only when the system is given reliable feedback and that feedback is used in a properly evaluated future run.

The demo provides `POST /api/outcomes` for a human to record a verified outcome. For example, after confirming the real outcome for a synthetic customer, record whether that customer actually churned. The API stores the observation and updates the synthetic training label. A future approved run can then include the corrected label.

Example request:

```bash
curl -X POST http://localhost:8000/api/outcomes \
  -H "Content-Type: application/json" \
  -d '{
    "objective": "customer_churn",
    "entity_ref": "CUS-00001",
    "actual_outcome": false,
    "source_run_id": "<RUN_ID>",
    "note": "Verified by the synthetic customer-success exercise"
  }'
```

Replace `<RUN_ID>` with the run identifier whose synchronized prediction you are verifying. The API rejects feedback unless it matches a prediction that passed the human-approved writeback gate. Use `true` only when the observed label is positive (the customer churned). The example is illustrative; do not copy an invented outcome into a live system.

Check feedback quality with:

```bash
curl http://localhost:8000/api/monitoring
```

Then start a new run. The next training execution reads the corrected source label and compares its new candidate model using the holdout evaluation. The system does not automatically promote the new model. It still requires human review and approval.

## Part 9 — give the system supervisory instructions

Try these instructions in separate runs:

- `Prioritize recall.`
- `Prioritize precision.`
- `Do not use satisfaction_score.`
- `Exclude monthly_spend.`

The first two change the classification threshold in a documented way. The latter instructions remove an explicitly named feature. Other free-text instructions are retained for context but are not guaranteed to change code or policy. Add new deterministic controls only after documenting their meaning, testing them and updating the approval screen.

## Part 10 — explore the technical services

| Service | What to inspect |
|---|---|
| FastAPI | `/docs` lists the routes and request/response formats |
| PostgreSQL | Stores source records, runs, approvals, predictions, model registry and feedback |
| LangGraph | Runs the stages and remembers where it paused for approval |
| SQLite checkpoint file | Stores LangGraph checkpoints for this small single-process prototype |
| MLflow | Stores candidate experiment parameters, metrics and model files |
| Streamlit | Shows the business process and approval requests |
| scikit-learn | Provides the two baseline model pipelines |
| LangChain + Ollama | Optional local language model for richer question suggestions |

## Part 11 — test a rejection path

Start another run. Reject the business-question approval. The workflow should stop and not train a model. Start a third run and reject model promotion. It should not proceed to the final writeback stage. A fourth run can be allowed to promote a model but rejected at writeback; that must leave the prediction records un-synchronized.

Testing rejection is as important as testing approval. The system is designed to pause by default at the defined gates.

## Part 12 — what to build next

A business-ready version should add the following only after agreeing the use case and controls:

1. Time-aware sales forecasting and inventory demand modelling.
2. Customer lifetime-value modelling with an agreed definition and observation horizon.
3. Campaign attribution with explicit attribution assumptions.
4. Real, least-privilege connectors for CRM, ERP, support and marketing platforms.
5. An identity system with named roles and approval permissions.
6. A model-monitoring service for drift, data quality, performance and business impact.
7. A production-grade checkpoint store such as PostgreSQL-backed LangGraph checkpoints.
8. A controlled deployment process with model version pinning and rollback.

Do not connect the prototype to real business data until the integration, privacy, security, model-risk and operational reviews are complete.
