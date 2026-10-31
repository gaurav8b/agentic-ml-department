# Replacing the Synthetic Business Systems with Real Systems

This project deliberately simulates a CRM, lead-generation application, ERP/commerce platform, marketing automation system and support platform. This lets a new user learn the process without exposing company information or risking a live system.

## 1. Start with one real system and read-only access

Do not connect every business application at once. Choose one data source with a clear owner and a clear approved use. For an initial ML pilot, a controlled warehouse view or read-only replica is usually easier to govern than direct access to a transactional production database.

## 2. Complete this connector worksheet

| Question | Example answer |
|---|---|
| Business system | CRM platform |
| Process owner | Head of Sales |
| Data owner | CRM administrator |
| Business purpose | Lead conversion prioritization |
| Permitted records | Open leads from an approved region |
| Permitted fields | Source, industry, company size, budget band, engagement and creation date |
| Excluded fields | Free-text notes containing sensitive personal information |
| Access type | Read-only service identity |
| Connection method | Vendor API or approved warehouse view |
| Rate limit | Confirmed with the system owner |
| Refresh frequency | Daily, subject to source-system behavior |
| Failure action | Stop and notify owner; do not make up missing records |
| Security controls | Secret manager, TLS, audit log and least privilege |
| Approver | Named person/role approved by the business |

## 3. Use the connector pattern, not unrestricted access

The current `connectors.py` module is intentionally small. In a real integration, create a dedicated adapter for each service with methods such as:

- `test_connection()` — verify access and report the service status.
- `describe_schema()` — list only approved objects and fields.
- `fetch_incremental(since)` — fetch records changed since the last successful run.
- `validate_record(record)` — check required fields and data types.
- `prepare_writeback(records)` — generate a preview without changing the destination.
- `execute_writeback(batch, approval)` — perform an approved, idempotent operation and return a receipt.

A language model should not receive a general SQL console or unrestricted HTTP credentials. Expose named, validated operations instead.

## 4. Real writeback design

Before adding a write endpoint, define:

- The exact fields to create or update.
- Which identifier matches a record safely.
- What happens for a missing or duplicate identifier.
- How an approval is associated with the batch.
- How repeated requests avoid duplicate updates.
- Whether the change can be undone.
- How to record the destination response.
- How to reconcile partial failures.

Use an outbox or job table for larger integrations. The workflow should record the request, obtain approval, submit the operation, capture the destination receipt and reconcile incomplete items. Never claim an external update succeeded until the destination confirms it.

## 5. Secrets and identities

- Store API tokens in a dedicated secret manager.
- Use service identities scoped to the required system resources.
- Rotate credentials and revoke them when no longer needed.
- Do not place tokens in prompts, model context, source files or logs.
- Do not let a user-supplied prompt change a connector's permission scope.
- Separate developer, test and production credentials.

## 6. Data protection

Before copying real data into this project or an ML environment, the company must determine the lawful basis and business purpose, retention period, access controls, privacy notices and any applicable regulatory requirements. Minimize data. Prefer aggregated or pseudonymized fields when they are sufficient. Do not send sensitive records to an external model provider unless that use has been approved.

## 7. Environment configuration

The demo uses environment variables for service locations. A production application should add a configuration layer per environment, for example:

- `DEV`: synthetic data and sandbox services.
- `TEST`: masked or approved test records.
- `PROD`: production connector identities, restricted network paths and monitored changes.

Production values belong in a secret manager or deployment platform's protected configuration, never in `.env` committed to Git.

## 8. Production rollout order

1. Data-owner approval and connector threat review.
2. Read-only connection in development.
3. Field-level data quality and lineage testing.
4. Read-only pilot with real users.
5. Model validation on a representative future period.
6. Model-risk, privacy, security and legal reviews.
7. Score preview and reconciliation test.
8. Human-approved limited writeback to a sandbox.
9. Controlled production pilot with a manual override.
10. Measured expansion after the owner accepts the business results.

## 9. What remains to be built for a real integration

This repository provides the connector shape and synthetic endpoints. It does not ship OAuth flows, vendor-specific Salesforce/HubSpot/SAP/ServiceNow integrations, production secrets management, enterprise identity, enterprise-grade audit immutability or a production change-management integration. Those require implementation and authorization in the target organization.
