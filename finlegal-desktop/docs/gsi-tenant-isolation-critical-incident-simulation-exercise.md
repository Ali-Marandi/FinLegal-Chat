# FinLegal-Chat v0.2.0 GSI Tenant-Isolation Critical Incident Simulation
## Tabletop Exercise Scenario

**Exercise type:** Facilitated tabletop with optional technical sandbox replay  
**Audience:** GSI engineering and security leads, GSI solution architects, enterprise customer engineering/security, FinLegal Security, Release Engineering, Privacy, Customer Success, Legal, and Partner Operations  
**Duration:** 90 minutes exercise plus 30 minutes debrief  
**Classification:** Internal exercise; use synthetic identifiers and synthetic data only

## Exercise purpose

This exercise tests whether the GSI partner and FinLegal teams can detect, contain, escalate, investigate, communicate, remediate, and safely recover from a simulated cross-tenant access failure during a v0.2.0 controlled pilot. It is specifically designed to validate the Critical-stop escalation matrix, the customer remediation runbook, the automated compliance audit alert path, and the evidence-preservation standard.

The exercise is not a production penetration test. No real customer data, credentials, production tenant, production endpoint, signing key, or live customer notification should be used. Facilitators must label all records **SIMULATION — DO NOT ACTION** and notify participants before the exercise begins.

## Scenario inject

At 10:15 Pacific Time, the weekly compliance audit for GSI partner **Northstar Integrators** reports a Critical result for deployment `SIM-GSI-042` in region `eu-west`. The failed checks are:

- `R-030`: Tenant-isolation test is not confirmed.
- `R-031`: Cross-tenant access denial is not confirmed.

The partner’s sandbox test team reports that a user from synthetic tenant `TENANT-A` received a search result citation referencing synthetic tenant `TENANT-B`. The result was generated through the approved search workflow, not an administrator-only endpoint. No real customer data is present. The GSI has a controlled pilot scheduled to expand to 25 users in four hours.

The audit webhook has delivered a Critical alert to the on-call engineering lead. The partner has not yet distributed a new installer, and the current artifact hash, signature, and provenance checks are valid. The initial facts do not establish whether the issue is caused by tenant-context propagation, search-index scope, cache keying, stale test data, or a test harness defect.

## Exercise objectives

| Objective | Success condition |
|---|---|
| Detection and acknowledgement | The GSI and FinLegal on-call owners acknowledge the Critical alert and open a simulation incident within 15 minutes. |
| Containment | The affected search workflow and scheduled pilot expansion are paused; no participant disables security controls or deletes evidence. |
| Escalation | Customer Security, GSI Security, FinLegal Security, Release Engineering, Privacy, and the Incident Commander are identified according to the matrix. |
| Evidence preservation | Participants record tenant IDs, request IDs, timestamps, test inputs, audit JSON, logs, configuration version, and distribution status using synthetic data only. |
| Customer-safe communication | A holding message states what is known, what is paused, and the next update time without calling the product unsafe, safe, compliant, or unaffected. |
| Remediation decision | The team chooses a bounded synthetic-data investigation and defines the required positive/negative retests. |
| Recovery gate | Participants do not resume the pilot until independent Security review, customer approval, and a documented go/no-go decision are present. |

## Timeline and facilitator injects

| Time | Inject | Expected response |
|---|---|---|
| T+0 | Automated audit emits Critical webhook alert. | Acknowledge, classify, open incident, pause affected scope. |
| T+10 min | GSI says the customer pilot expansion is commercially time-sensitive. | Maintain the hold; explain that commercial urgency does not override tenant isolation. |
| T+20 min | A developer proposes clearing the search cache and rerunning the same test. | Preserve the original state first; do not overwrite evidence; define a controlled reproduction. |
| T+30 min | Customer Security asks whether any production data was exposed. | State that the exercise has synthetic data and that real-world exposure is not yet determined; describe the investigation boundary. |
| T+40 min | A second synthetic tenant shows no issue in a single-user test. | Do not close the incident; require concurrency, cache, retry, export, connector, and negative authorization tests. |
| T+55 min | Product asks whether the unaffected document-upload workflow can continue. | Permit only if Security and the customer owner define and approve a reduced scope with the affected search path excluded. |
| T+70 min | Engineering produces a fix for tenant-context propagation. | Require code review, clean test evidence, positive and negative tests, independent Security review, and updated deployment record. |
| T+85 min | GSI requests permission to expand the pilot. | Require formal go/no-go approval, customer change record, rollback owner, and closure of Critical findings. |

## Required actions by role

**GSI Engineering Lead.** Acknowledge the alert, pause the affected scope and pilot expansion, preserve synthetic evidence, identify partner-side users and systems that accessed the test, and provide the incident record to FinLegal.

**GSI Security/Risk.** Confirm that no real customer data or shared credentials were used, preserve partner logs and access records, and coordinate the customer security contact.

**Customer Engineering/Security.** Confirm customer-side change status, endpoint and identity controls, approved pilot scope, and whether any customer data entered the affected workflow.

**FinLegal Security.** Own severity, containment, authorization analysis, incident evidence, and independent retest approval.

**FinLegal Release Engineering.** Confirm artifact integrity, freeze any affected release or configuration publication, and record the source revision and workflow evidence.

**FinLegal Privacy.** Confirm data classes and residency impact; in this exercise, confirm that synthetic data was used and that no real transfer assessment is required.

**Incident Commander.** Control the timeline, decision log, communications cadence, and transition between containment, investigation, remediation, recovery, and closure.

## Required evidence packet

The facilitator should collect the following synthetic evidence:

1. The audit JSON output showing `R-030` and `R-031` failure.
2. The webhook alert payload and delivery timestamp.
3. Test tenant IDs, synthetic user IDs, roles, request IDs, search terms, citations, and timestamps.
4. Relevant application, authorization, cache, search-index, connector, and audit logs.
5. The configuration and source revision under test.
6. Distribution and pilot status, including proof that expansion was paused.
7. The holding message and recipient list.
8. The remediation diff or change description.
9. Positive and negative retest outputs, including concurrency and retry tests.
10. Security, customer, GSI, and release go/no-go approvals.

## Decision points

The team must answer four questions explicitly:

**Was the failure real or a test-harness defect?** Until the evidence establishes otherwise, treat the result as a real Critical stop.

**Could another tenant or customer have been affected?** Scope must be based on logs, code paths, cache/index behavior, and the relevant time window—not on the absence of a second report.

**Can an unaffected workflow continue?** Only under a documented reduced scope that excludes the affected path and uses approved data, identity, region, and support controls.

**What proves recovery?** The original failure is reproduced or explained, the fix passes positive and negative tests, Security independently reviews the result, the customer accepts the change, and the deployment record is updated.

## Scoring rubric

| Score | Meaning |
|---|---|
| Green | Critical alert acknowledged within 15 minutes; scope paused; evidence preserved; correct owners engaged; no bypasses; recovery gate followed. |
| Amber | Response completed but with delay, unclear ownership, incomplete evidence, or a communication defect that did not weaken containment. |
| Red | Team continued the affected rollout, used real customer data during investigation, deleted/overwrote evidence, bypassed authorization or endpoint controls, or resumed without required approvals. |

## Debrief questions

1. Did the webhook alert reach the correct on-call owner without exposing sensitive customer data?
2. Was the GSI clear about the difference between a Critical stop and a routine defect?
3. Could every participant identify the current incident owner and next update time?
4. Did the evidence packet support tenant scope analysis without using real customer content?
5. Were customer, Privacy, Security, Release Engineering, and Legal decision rights clear?
6. Did the fallback discussion preserve tenant isolation, residency, identity, retention, and release-integrity controls?
7. Which checklist field, integration, runbook instruction, or contact route needs improvement?

## References

[1]: FinLegal-Chat_v0.2.0_GSI_Critical_Stop_Escalation_Matrix_and_Contact_Protocol.md "FinLegal-Chat v0.2.0 GSI Critical Stop Escalation Matrix and Contact Protocol"

[2]: FinLegal-Chat_v0.2.0_Customer_Tenant_Isolation_and_Data_Residency_Failure_Remediation_Runbook.md "FinLegal-Chat v0.2.0 Customer Tenant Isolation and Data Residency Failure Remediation Runbook"

[3]: FinLegal-Chat_v0.2.0_Enterprise_Deployment_Stop_Conditions_Cheat_Sheet.md "FinLegal-Chat v0.2.0 Enterprise Deployment Stop Conditions Cheat Sheet"
