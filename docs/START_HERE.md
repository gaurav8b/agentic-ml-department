# Start Here — What Have We Built?

## Imagine you have hired a small machine-learning department

In a conventional company, people in several departments use separate software systems:

- Sales and customer information lives in a CRM.
- New prospects arrive through lead-generation and marketing tools.
- Orders and revenue are recorded in an ERP or commerce platform.
- Customer complaints and service history live in a support system.

The machine-learning department needs approved access to relevant information from these systems. It then looks for useful business questions, prepares the data, tests possible prediction methods, explains the results and asks the business owner to approve the next step.

This project builds a small, fictional version of that department.

## What does “agentic” mean?

An AI agent is a software worker that can receive a goal, use approved tools, inspect the result and decide which permitted step to take next. An agentic workflow coordinates several such steps and workers. It is not a licence to do anything without limits.

In this project, the workflow has specialist responsibilities:

| Role | Plain-English responsibility |
|---|---|
| Workflow supervisor | Makes sure work happens in the right order and stops at approval gates |
| Data steward | Finds available business sources and checks data quality |
| Business analyst | Suggests questions worth answering and explains why they matter |
| ML engineer | Trains and compares prediction models |
| Model reviewer | Checks test results and highlights weaknesses |
| Integration operator | Prepares predictions for the business systems and waits for permission |
| Business-value reviewer | Summarizes the potential business value and records follow-up learning |

The first version implements these responsibilities as explicit workflow steps. Some are deterministic software functions; optional language-model advice can be enabled separately.

## What should you do first?

1. Read the installation section of the main README.
2. Start the project with Docker Compose.
3. Open the dashboard.
4. Start a customer churn workflow.
5. Approve the business question.
6. Inspect the model's test results.
7. Approve promotion, then separately approve CRM writeback.
8. Explore the API documentation and MLflow experiment screen.

You can complete the first demonstration without writing code or paying for an AI model API.

## Five words you will see frequently

- **Database:** an organized store for business records.
- **Model:** a program trained on examples to estimate an outcome for new records.
- **Training:** showing a model historical examples so it can learn patterns.
- **Prediction:** a model's estimate, such as a probability that a customer may leave.
- **Approval gate:** a deliberate pause where a person must approve before the next stage proceeds.

## What is not automatic?

A prediction is not a business decision. A high churn score does not prove that a customer will leave. A high lead score does not guarantee a sale. The system prepares prioritization information; a qualified employee decides what action is appropriate.
