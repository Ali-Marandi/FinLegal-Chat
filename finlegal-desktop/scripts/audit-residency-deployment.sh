#!/usr/bin/env bash
# FinLegal-Chat v0.2.0 GSI deployment residency audit
# Usage: ./audit-residency-deployment.sh deployment-record.json [--json]
set -euo pipefail

INPUT="${1:-}"
OUTPUT_JSON=0
if [[ "${2:-}" == "--json" ]]; then OUTPUT_JSON=1; fi

if [[ -z "$INPUT" || ! -f "$INPUT" ]]; then
  echo "Usage: $0 deployment-record.json [--json]" >&2
  exit 2
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: jq is required" >&2
  exit 2
fi

errors=0
warnings=0
results='[]'

add_result() {
  local id="$1" status="$2" message="$3" severity="$4"
  results=$(jq --arg id "$id" --arg status "$status" --arg message "$message" --arg severity "$severity" \
    '. + [{id:$id,status:$status,severity:$severity,message:$message}]' <<<"$results")
  case "$status" in
    FAIL) errors=$((errors+1));;
    WARN) warnings=$((warnings+1));;
  esac
}

required_string() {
  local id="$1" path="$2" label="$3"
  local value
  value=$(jq -r "$path // empty" "$INPUT")
  if [[ -z "$value" || "$value" == "null" ]]; then
    add_result "$id" FAIL "$label is missing" HIGH
  else
    add_result "$id" PASS "$label recorded" INFO
  fi
}

required_true() {
  local id="$1" path="$2" label="$3"
  if [[ "$(jq -r "$path // false" "$INPUT")" == "true" ]]; then
    add_result "$id" PASS "$label confirmed" INFO
  else
    add_result "$id" FAIL "$label is not confirmed" HIGH
  fi
}

array_nonempty() {
  local id="$1" path="$2" label="$3"
  if [[ "$(jq -r "(($path // []) | length)" "$INPUT")" -gt 0 ]]; then
    add_result "$id" PASS "$label recorded" INFO
  else
    add_result "$id" FAIL "$label must contain at least one approved entry" HIGH
  fi
}

# 1. Deployment identity and scope.
required_string R-001 '.deployment_id' 'Deployment ID'
required_string R-002 '.customer_id' 'Customer identifier'
required_string R-003 '.gsi_partner' 'GSI partner'
required_string R-004 '.deployment_class' 'Deployment class'
required_string R-005 '.artifact.version' 'Artifact version'
required_string R-006 '.artifact.source_sha' 'Source SHA'

# 2. Region and approved data-flow.
required_string R-010 '.residency.customer_region' 'Customer region'
required_string R-011 '.residency.data_region' 'Primary data region'
required_string R-012 '.residency.backup_region' 'Backup region'
required_string R-013 '.residency.support_region' 'Support region'
required_true R-014 '.residency.data_flow_approved' 'Data-flow approval'
required_true R-015 '.residency.cross_border_transfer_reviewed' 'Cross-border transfer review'

if [[ "$(jq -r '.residency.customer_region' "$INPUT")" != "$(jq -r '.residency.data_region' "$INPUT")" ]]; then
  add_result R-016 FAIL 'Customer region and primary data region differ without an explicit exception path' CRITICAL
else
  add_result R-016 PASS 'Customer region matches primary data region' INFO
fi

if [[ "$(jq -r '.residency.backup_region' "$INPUT")" != "$(jq -r '.residency.data_region' "$INPUT")" ]]; then
  if [[ "$(jq -r '.residency.backup_exception_approved // false' "$INPUT")" != "true" ]]; then
    add_result R-017 FAIL 'Backup region differs from primary region without approved exception' HIGH
  else
    add_result R-017 PASS 'Backup-region exception is approved and recorded' INFO
  fi
else
  add_result R-017 PASS 'Backup region matches primary region' INFO
fi

# 3. Data classes, processing routes, and subprocessors.
array_nonempty R-020 '.residency.data_classes' 'Data classes'
array_nonempty R-021 '.residency.approved_subprocessors' 'Approved subprocessors'
required_string R-022 '.residency.model_route' 'Model route'
required_string R-023 '.residency.log_route' 'Log route'
required_string R-024 '.residency.telemetry_route' 'Telemetry route'

if [[ "$(jq -r '.residency.unapproved_external_routes // [] | length' "$INPUT")" -gt 0 ]]; then
  add_result R-025 FAIL 'Unapproved external data routes are present' CRITICAL
else
  add_result R-025 PASS 'No unapproved external data routes recorded' INFO
fi

# 4. Tenant isolation and identity controls.
required_true R-030 '.controls.tenant_isolation_tested' 'Tenant-isolation test'
required_true R-031 '.controls.cross_tenant_access_denied' 'Cross-tenant access denial'
required_true R-032 '.controls.identity_configured' 'Identity configuration'
required_true R-033 '.controls.mfa_or_customer_equivalent' 'MFA or customer-equivalent control'
required_true R-034 '.controls.joiner_mover_leaver_tested' 'Joiner/mover/leaver test'

# 5. Retention, deletion, backup, and support.
required_true R-040 '.controls.retention_policy_approved' 'Retention policy approval'
required_true R-041 '.controls.deletion_tested' 'Deletion test'
required_true R-042 '.controls.backup_expiry_defined' 'Backup expiry definition'
required_true R-043 '.controls.legal_hold_path_defined' 'Legal-hold path'
required_true R-044 '.controls.support_access_reviewed' 'Support-access review'
required_true R-045 '.controls.incident_route_tested' 'Incident route test'

# 6. Release evidence and approvals.
required_string R-050 '.artifact.sha256' 'Artifact SHA-256'
required_true R-051 '.artifact.signature_verified' 'Platform signature verification'
required_true R-052 '.artifact.provenance_verified' 'Provenance verification'
required_true R-053 '.approvals.gsi_engineering' 'GSI engineering approval'
required_true R-054 '.approvals.customer_engineering' 'Customer engineering approval'
required_true R-055 '.approvals.finlegal_security' 'FinLegal Security approval'
required_true R-056 '.approvals.finlegal_privacy' 'FinLegal Privacy approval'
required_true R-057 '.approvals.rollback_owner_named' 'Rollback owner assignment'

# 7. Preview/pilot boundary.
case "$(jq -r '.deployment_class' "$INPUT")" in
  preview|controlled_pilot) add_result R-060 PASS 'Deployment class is bounded by preview/pilot controls' INFO;;
  production) required_true R-061 '.approvals.production_go_no_go' 'Production go/no-go approval';;
  *) add_result R-060 FAIL 'Deployment class must be preview, controlled_pilot, or production' HIGH;;
esac

if [[ "$OUTPUT_JSON" -eq 1 ]]; then
  jq -n --arg input "$INPUT" --argjson errors "$errors" --argjson warnings "$warnings" --argjson results "$results" \
    '{input:$input,failed_checks:$errors,warnings:$warnings,passed:($errors==0),results:$results}'
else
  jq -r '.[] | "\(.status) [\(.severity)] \(.id): \(.message)"' <<<"$results"
  echo
  echo "Summary: failed_checks=$errors warnings=$warnings"
fi

if [[ "$errors" -gt 0 ]]; then exit 1; fi
exit 0
