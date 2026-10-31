# General Standard Operating Procedure (SOP)
## How to design, build, govern and operate an enterprise Agentic AI workflow

**Audience:** a business owner, department head or intelligent non-technical project sponsor. No programming knowledge is assumed.

**Purpose:** provide one repeatable method for turning a business process into a safe, measurable, human-supervised AI workflow. The machine-learning department in this repository is the worked innovation prototype. The same method can be used for IT service management, software engineering, finance operations, procurement, customer service and other departments.

---

## 1. The central idea

Do not begin by asking, “Which AI agent should we buy?” Begin by asking, “Which business job should become faster, more accurate or more consistent, and what must remain under human control?”

An agentic system is a team of software workers operating under a defined process. It can inspect information, make recommendations, call approved tools and complete permitted tasks. A reliable system also knows when it must stop and ask a person.

The enterprise pattern is:

1. A person defines the business objective and boundaries.
2. The system discovers approved information sources.
3. The system checks that the information is suitable for the task.
4. The system proposes a work plan and asks questions when requirements are incomplete.
5. A person approves the objective and material choices.
6. Specialist agents carry out their assigned work.
7. Independent checks test the result.
8. A person approves any material model release or business-system action.
9. The system records what happened and compares it with the intended business result.
10. Lessons are used to propose improvements; material policy changes require approval.

**Operating principle:** automate preparation, analysis, repetitive execution and evidence collection; retain human authority over objectives, exceptions, consequential decisions and irreversible actions.

## 2. Who does what?

A small project still needs named responsibility. The same individual may hold more than one role, but the duties should remain distinct.

| Role | What the person/system is responsible for | Example |
|---|---|---|
| Executive sponsor | Owns the business outcome, budget and risk appetite | Head of Sales |
| Process owner | Explains the current process and approves operational changes | Customer Success Manager |
| Product/project owner | Organizes requirements, milestones and acceptance | Project Lead |
| Data owner | Approves access, permitted use, definitions and retention | CRM/Data Manager |
| AI workflow supervisor | Routes work, tracks progress and stops at policy gates | LangGraph workflow |
| Specialist agents | Complete bounded analysis or execution tasks | Data profiler, model builder, code reviewer |
| Independent reviewer | Challenges work and checks the evidence | Model reviewer / QA agent |
| Security/privacy owner | Reviews access, sensitive data, credentials and auditability | Security lead |
| Operations owner | Monitors production behavior and handles incidents | Department operations |

No agent may approve its own high-impact action. A model that recommends a discount must not silently grant the discount unless a separately approved policy explicitly permits that exact range and action.

## 3. Stage 0 — choose the business problem

### 3.1 Describe the work in ordinary language

Write a one-page problem statement. It must answer:

- Who experiences the problem?
- What happens today?
- What is slow, costly, inconsistent or frequently missed?
- What should be better after the project?
- What is the consequence of a wrong recommendation?
- Who can approve the result?

Avoid starting with a technical solution such as “we need a chatbot” or “we need five agents.” A tool is useful only when it improves a defined process.

### 3.2 Define a measurable outcome

Choose one main measure and a small number of supporting measures. Examples:

| Department | Main measure | Supporting measures |
|---|---|---|
| Machine learning | Incremental value from an approved prediction use case | Model quality, coverage, cost, drift, time to insight |
| IT operations | Time to restore service | First-contact resolution, repeat incidents, escalation rate |
| Software engineering | Time from approved requirement to safe release | Defect escape rate, test coverage, review time, rollback rate |
| Customer service | Time to resolve a request while maintaining quality | Reopen rate, customer satisfaction, escalation rate |

Set a baseline before automating. Without a baseline, you cannot tell whether the project helped.

### 3.3 Decide whether AI is appropriate

Use automation only when the task has enough reliable information, a clear success test and an acceptable failure path. A deterministic rule or ordinary software may be better than an LLM for calculations, permissions, money movement and other exact operations.

## 4. Stage 1 — map the business process and systems

Draw the process as it works today, not as management wishes it worked. Identify every system that supplies or receives information.

For each system, document:

- System name and business owner.
- Information it contains and who is allowed to use it.
- How the AI application will read or write the information.
- Whether access is read-only or write-enabled.
- Data refresh frequency and known delays.
- Rate limits, outages and error handling.
- Personal, confidential or regulated data present.
- How access is revoked and credentials rotated.

For this prototype, the fictional company has five connected systems:

| System | Typical information | Prototype connection |
|---|---|---|
| CRM | Customers, accounts, sales contacts | Synthetic customer and lead tables |
| Lead generation | New prospects and engagement | Synthetic lead records through CRM/lead endpoints |
| ERP / commerce | Orders, products, revenue and fulfilment | Synthetic sales orders |
| Marketing automation | Campaign activity and spend | Synthetic campaigns |
| Customer support | Tickets, service history and satisfaction | Synthetic support tickets |

**Important:** a system being technically reachable does not mean the AI has permission to use every field. Obtain data-owner approval before connecting a real system.

## 5. Stage 2 — design the agent team and workflow

### 5.1 Use a supervisor plus bounded specialists

Begin with one workflow supervisor. Add specialist agents only when the responsibilities are sufficiently different to benefit from separate instructions, tools or review criteria.

A reusable structure is:

- **Supervisor:** interprets the approved goal, delegates work, tracks dependencies and decides which workflow step is next.
- **Discovery specialist:** finds permitted systems, tables, documents and APIs.
- **Analysis specialist:** profiles information and identifies gaps.
- **Business analyst:** translates a department need into testable questions.
- **Execution specialist:** performs the bounded task.
- **Reviewer:** independently checks the work and asks for corrections.
- **Integration specialist:** prepares external actions, but only executes after approval.
- **Monitoring specialist:** compares outcomes with targets and proposes improvements.

Do not create agents for cosmetic reasons. A single well-designed workflow with a few specialists is usually easier to test than a swarm of loosely defined agents.

### 5.2 Describe every agent before writing code

For every role, write:

1. Name and purpose.
2. Inputs it may read.
3. Tools it may call.
4. Actions it may take.
5. Actions it must never take.
6. Required output format.
7. How success is checked.
8. Who receives the output.
9. When it must ask for human input.

A specialist must not invent missing facts. It should return “unknown” and ask the supervisor for clarification.

### 5.3 Make the workflow explicit

Use a visible sequence with named states. A useful generic workflow is:

`Request → Discover → Validate Inputs → Plan → Human Approval → Execute → Review → Remediate → Human Release Approval → Integrate → Measure → Learn`

Use ordinary code for fixed rules and calculations. Use an LLM for language interpretation, summarization, question generation and bounded decisions where ambiguity is expected. Never delegate authorization to a language model.

## 6. Stage 3 — connect tools and information safely

Create a connector for each source system. A connector should expose a small, documented set of operations rather than unrestricted access to the entire application.

### Connector checklist

- [ ] The business owner has approved the connection.
- [ ] The connector uses a named service identity, not a user's personal login.
- [ ] Access is limited to necessary tables, fields and endpoints.
- [ ] Read access is separate from write access.
- [ ] Credentials are kept outside source code and rotated.
- [ ] Inputs are validated and outputs are logged.
- [ ] Retries are limited and safe; write operations are idempotent where possible.
- [ ] Rate limits and outages are handled.
- [ ] Sensitive fields are masked or excluded when not required.
- [ ] There is a tested way to disable the connector.

Start with read-only access. Introduce write access only after the read-only workflow has passed testing and the business owner has approved the exact action.

## 7. Stage 4 — discover and assess the data

The AI department should inventory available datasets, row counts, field names, data types, missing values, duplicate records, date ranges and obvious quality issues.

It should produce a data catalogue in ordinary language. For each field, explain what it means, where it came from and whether it can be used for the approved purpose.

### Data-quality checks

- Completeness: are required values missing?
- Validity: are values within sensible ranges?
- Consistency: do different systems use the same definitions?
- Uniqueness: are duplicate customers or transactions present?
- Timeliness: how old is the information?
- Coverage: which customer groups or time periods are absent?
- Lineage: can the system show where a result came from?

Do not let the AI silently repair material source data. It should propose a correction, explain the impact and record approval for changes that affect the source system.

## 8. Stage 5 — ask and approve the business questions

A dataset is not a business objective. Before building a model or automating a workflow, the system should offer a short list of questions that the available information may answer.

For a machine-learning use case, every proposed question must identify:

- The entity being predicted (customer, lead, transaction, machine, etc.).
- The outcome (churn, conversion, delay, demand, default, etc.).
- The prediction horizon (for example, the next 30 days).
- The information available at prediction time.
- The person who can act on the prediction.
- The business action that might follow.
- The measure by which success will be judged.
- What must not be inferred from the prediction.

The business owner should approve one question at a time. “Can we predict churn?” is incomplete unless the business also defines what churn means, the time window and what action is allowed.

If required information is missing, ask a question rather than fabricating an answer. Record the user's answer as an explicit project instruction with date, owner and scope.

## 9. Stage 6 — prepare the data and prevent leakage

Prepare a reproducible dataset for the approved problem. Keep a record of:

- Source tables and extraction time.
- Join logic and entity matching rules.
- Included and excluded fields.
- Missing-value treatment.
- Outlier and invalid-value treatment.
- Label definition and observation window.
- Training, validation and test dates or split logic.
- Any data removed for privacy or policy reasons.

**Data leakage** occurs when the training process uses information that would not have been available at the moment a real prediction is required. For example, a model predicting whether a lead will convert must not use a field that is only populated after the sale closes.

Use time-based evaluation for future-facing predictions when a random split would make future information leak into the past. For customer or account data, keep related records together if separate rows from one entity could otherwise appear in both training and test data.

## 10. Stage 7 — build and compare simple models first

Begin with interpretable baselines. Do not choose a complex model just because the name sounds advanced.

A sensible first sequence is:

1. Establish a simple baseline.
2. Train one or two suitable candidate models.
3. Evaluate them on data not used to fit the model.
4. Compare the measures that match the business cost of errors.
5. Inspect important input signals and unexpected behavior.
6. Record code, data version, model settings, metrics and model files.
7. Ask a human reviewer to approve a candidate before any production use.

Classification measures such as precision and recall are not interchangeable:

- Precision asks: among the records flagged, how many were actually positive?
- Recall asks: among the actual positive records, how many did the model find?
- AUC summarizes ranking quality across thresholds; it does not guarantee useful business decisions.

For a real business, choose the threshold based on the cost of false alarms, missed opportunities and the team's capacity to act. Do not use accuracy alone when positive outcomes are rare.

## 11. Stage 8 — conduct an independent review

A model reviewer should check:

- Whether the approved question was answered.
- Whether the data definition and prediction horizon are correct.
- Whether the test set is independent and representative.
- Whether leakage or target contamination exists.
- Whether performance is stable across meaningful groups and time periods.
- Whether important features are available at prediction time.
- Whether confidence and uncertainty are communicated honestly.
- Whether the model adds value over the existing process.
- Whether there is a safe fallback when the model is unavailable or unreliable.

A reviewer must be able to reject the model and state what must be fixed. A model should not pass merely because an agent says it is good.

## 12. Stage 9 — approve the model and business action separately

There are two different decisions:

1. **Model approval:** Is this model suitable to be made available for the intended use?
2. **Business-action approval:** Is this particular action permitted for this record, customer or event?

An approved model does not automatically authorize every possible use of its scores. Define permitted users, use cases, threshold ranges, review periods and prohibited decisions.

For the prototype, the model must pass a basic test-quality rule and receive a human promotion decision. The final score writeback is a separate approval. The model quality rule is only a demonstration threshold, not a production standard.

## 13. Stage 10 — integrate results into business systems

Prepare the exact records to be written, show the destination and provide a preview. Before writeback, confirm:

- What fields will be sent?
- Which records will be updated?
- What happens if a record is not found?
- Is the action reversible?
- Can a repeated request create duplicate updates?
- Who approved this exact action?
- Can the business team verify that the destination received the correct data?

Start with a pilot or sandbox. Use a small batch. Require a human approval before broad rollout. Keep rollback instructions and preserve the previous value when appropriate.

## 14. Stage 11 — measure actual business outcomes

Do not stop at model accuracy. The goal is better business performance.

Record what happened after a team acted on a recommendation. Examples:

- Did the at-risk customer remain active?
- Did the prioritized lead convert?
- Did the recommended intervention cost more than the value it created?
- Did response time improve?
- Did the team ignore most alerts because there were too many?

Compare results with the pre-project baseline and, when possible, an appropriate control group. Clearly distinguish observed facts from estimates. A predicted probability multiplied by revenue is an exposure estimate, not guaranteed savings.

## 15. Stage 12 — improve from evidence, not self-assertion

The system may:

- Collect observed outcomes and corrections.
- Detect missing data or changing distributions.
- Compare model performance across runs.
- Summarize which recommendations were useful.
- Suggest new features, questions or workflow improvements.
- Create a proposed retraining or policy-change request.

The system must not silently change the business objective, permissions, thresholds, approval requirements or consequential operating policy. Those changes require an owner, documented reason, evaluation and approval.

A model update should pass the same review and approval process as the original model. Keep the previous approved version so that the business can roll back.

## 16. Stage 13 — operate the system

Create a production operating plan before rollout:

| Operating topic | Required procedure |
|---|---|
| Monitoring | Check availability, job failures, latency, cost, data quality and model performance |
| Access | Review identities, roles, keys and connector permissions regularly |
| Incidents | Stop unsafe actions, preserve logs, notify the owner and use manual fallback |
| Changes | Version prompts, code, data definitions, model files and approval rules |
| Backups | Test restoration of databases, checkpoints, model files and audit logs |
| Retraining | Run only on approved data with documented evaluation and release gates |
| Retirement | Disable a model/agent, revoke credentials and retain required audit evidence |

## 17. Stage 14 — prove the project before expanding it

Use progressive stages:

1. **Offline demo:** synthetic data, no external side effects.
2. **Read-only pilot:** real data with limited access; recommendations are advisory only.
3. **Human-approved writeback:** small number of controlled actions with a named approver.
4. **Limited production:** defined users, monitored performance and rollback.
5. **Broader deployment:** only after evidence supports expansion.

At each stage, define pass/fail criteria. Do not move to the next stage because a demonstration looked impressive.

## 18. Minimum project documents

Every enterprise agentic workflow should have these documents:

1. Business problem statement and target measures.
2. Process map and system inventory.
3. Data catalogue and permissions record.
4. Agent role cards and tool-access matrix.
5. Workflow and approval diagram.
6. Model/data evaluation plan, where applicable.
7. Test plan and test evidence.
8. Risk register and prohibited-action list.
9. Integration and rollback plan.
10. Operations and incident runbook.
11. Model/prompt/workflow change history.
12. Outcome and continuous-improvement review.

## 19. Acceptance checklist for the project sponsor

The project is ready for a controlled pilot only when all applicable items are true:

- [ ] There is a measurable business problem and a named business owner.
- [ ] Every connected system and permitted field is documented.
- [ ] The system can explain what it is doing and why.
- [ ] An agent cannot bypass the approval gates.
- [ ] The system asks a human when required information is missing.
- [ ] Every tool has limited permissions and validated inputs.
- [ ] Important outputs have independent checks.
- [ ] Failures, rejections and approvals are recorded.
- [ ] External writeback is previewed and authorized.
- [ ] A manual fallback and rollback method exist.
- [ ] Actual outcomes can be collected and reviewed.
- [ ] The project has an operational owner and review schedule.

## 20. How to reuse this SOP for other departments

Keep the governance and build method the same. Replace the business specialists, tools, data and acceptance tests.

| Department | Example specialist agents | Typical approval gates |
|---|---|---|
| Machine learning | Data profiler, business-question adviser, feature analyst, model builder, model reviewer | Target approval, model promotion, score writeback |
| IT operations | Service-desk triage, knowledge search, incident analyst, remediation executor, change reviewer | Priority/severity confirmation, remediation, change window |
| Software engineering | Requirements analyst, planner, coder, test engineer, security reviewer, release operator | Scope, code merge, deployment |
| Finance operations | Invoice reader, matching agent, exception analyst, reconciliation reviewer | Payment exception, journal posting, vendor change |
| Customer service | Intent classifier, knowledge assistant, response drafter, escalation reviewer | Customer-impacting response, refund or account change |

The underlying control pattern remains stable: discover → plan → approve → execute → review → approve action → measure → learn.

---

## Appendix A — reusable one-page agent card

Copy this template for every agent:

- **Agent name:**
- **Business purpose:**
- **Responsible owner:**
- **Inputs it may access:**
- **Tools it may use:**
- **Actions it may perform without approval:**
- **Actions requiring approval:**
- **Prohibited actions:**
- **Output format:**
- **Success checks:**
- **Failure / escalation rule:**
- **Audit information to retain:**

## Appendix B — reusable approval request

A good approval request should show:

- The exact decision requested.
- Why the decision is needed now.
- Evidence and relevant source references.
- What the system proposes.
- Known uncertainty and risk.
- What will happen if approved.
- What will happen if rejected.
- Whether the action can be undone.
- Who is authorized to decide.
