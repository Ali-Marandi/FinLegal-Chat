# FinLegal-Chat v0.2.0 GSI Data-Residency Compliance Audit Checklist

**Purpose.** This checklist defines the minimum evidence required before a GSI partner may install, pilot, redistribute, or expand FinLegal-Chat v0.2.0 for an enterprise customer. It is designed for a controlled preview and controlled-pilot process. It is not a certification and does not replace the customer’s legal, privacy, security, procurement, or regulatory review.

## Audit outcome model

A deployment is **Pass** only when every Critical and High check is confirmed, the evidence is attached to the deployment record, and the named FinLegal Security, FinLegal Privacy, GSI Engineering, and customer engineering approvers have signed the record. A **Conditional Pass** is permitted only for a bounded preview or controlled pilot with a documented exception, compensating control, expiry date, owner, and explicit prohibition on production expansion. A **Fail** requires containment and blocks installation, redistribution, or expansion.

| Outcome | Meaning | Required action |
|---|---|---|
| Pass | All required checks are complete and evidence is present. | Proceed only within the approved deployment class and region. |
| Conditional Pass | A non-Critical gap is accepted for a bounded preview or pilot. | Record exception, owner, expiry, compensating control, and rollback. |
| Fail | A Critical/High control is absent, contradictory, or unverified. | Stop, preserve evidence, remediate, and retest. |

## Required deployment record

The GSI must create one record per customer or controlled pilot containing the deployment ID, customer ID, GSI partner, deployment class, artifact version, source SHA, platform and architecture, release manifest, artifact SHA-256, workflow run, provenance result, customer region, data region, backup region, support region, data-flow diagram, approved subprocessors, model route, log and telemetry routes, data classes, identity configuration, retention/deletion record, rollback owner, support owner, incident contacts, and named approvals.

## Automated checks

Run the repository script:

```bash
chmod +x scripts/audit-residency-deployment.sh
scripts/audit-residency-deployment.sh deployment-record.json
scripts/audit-residency-deployment.sh deployment-record.json --json > residency-audit.json
```

The script fails closed when required fields are absent. It verifies deployment identity, region alignment, backup exceptions, approved routes and subprocessors, tenant isolation, identity controls, retention and deletion, backup expiry, support access, release evidence, approvals, and the preview/pilot/production boundary. The JSON output is suitable for attaching to the partner portal or implementation ticket.

## Manual evidence checklist

| ID | Control | Evidence | Owner | Severity |
|---|---|---|---|---|
| R-001–R-006 | Deployment and artifact identity | Deployment record, version, source SHA, platform, and approved distribution source | GSI Engineering | High |
| R-010–R-017 | Region and transfer alignment | Customer/data/backup/support regions, data-flow approval, transfer review, and exception record | GSI SA + FinLegal Privacy | Critical |
| R-020–R-025 | Data routes and subprocessors | Data classes, approved subprocessors, model/log/telemetry routes, and proof that no unapproved route exists | FinLegal Privacy + Security | Critical |
| R-030–R-034 | Tenant and identity isolation | Cross-tenant negative test, identity configuration, MFA/equivalent, and lifecycle test | GSI Engineering + Customer IT | Critical |
| R-040–R-045 | Lifecycle and operations | Retention, deletion, backup expiry, legal hold, support access, and incident-route evidence | Customer IT + FinLegal CS/Security | High |
| R-050–R-052 | Release integrity | SHA-256, platform signature/notarization, and provenance verification output | Release Engineering | Critical |
| R-053–R-057 | Approvals and rollback | GSI, customer, Security, Privacy, and rollback-owner approvals | Release Approver | High |
| R-060–R-061 | Deployment boundary | Preview/pilot label or production go/no-go record | FinLegal + Customer | High |

## Stop conditions

Stop immediately for a region mismatch without an approved exception, an unapproved external route, cross-tenant access, missing or invalid signing/provenance evidence, an exposed credential, an unsupported residency commitment, or a Critical/High test failure. Preserve the artifact, logs, JSON audit output, ticket references, and communications. Do not rename, repackage, retry blindly, or redistribute the affected build.

## Audit cadence and retention

Run the checklist before initial installation, after any artifact or configuration change, before expansion to a new region or customer tenant, after a material subprocessor/model-route change, and after an incident. Retain the signed audit record with the customer change record and release evidence according to the applicable customer retention schedule and legal-hold requirements.

## References

[1]: FinLegal-Chat_v0.2.0_GSI_Engineering_Rollout_Communication_Plan.md "FinLegal-Chat v0.2.0 GSI Engineering Rollout Communication Plan"

[2]: FinLegal-Chat_GSI_Solution_Architect_Validation_and_Sandbox_Protocol.md "FinLegal-Chat GSI Solution Architect Validation and Sandbox Protocol"

[3]: FinLegal-Chat_Enterprise_Client_GSI_Governance_and_Data_Residency_Notification_Template.md "FinLegal-Chat Enterprise Client GSI Governance and Data Residency Notification Template"

[4]: FinLegal-Chat_v0.2.0_GitHub_Actions_Supply_Chain_Hardening_Review.md "FinLegal-Chat v0.2.0 GitHub Actions Supply Chain Hardening Review"
