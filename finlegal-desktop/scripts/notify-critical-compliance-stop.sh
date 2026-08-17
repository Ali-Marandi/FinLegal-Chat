#!/usr/bin/env bash
# FinLegal-Chat v0.2.0 Critical compliance-stop webhook notifier
# Usage: notify-critical-compliance-stop.sh audit-result.json [deployment-record.json]
# Required: FINLEGAL_ALERT_WEBHOOK_URL
# Optional: FINLEGAL_ALERT_WEBHOOK_TOKEN, FINLEGAL_ALERT_TIMEOUT_SECONDS, FINLEGAL_ALERT_RETRIES, FINLEGAL_ALERT_DRY_RUN=1
set -euo pipefail

INPUT="${1:-}"
RECORD="${2:-}"
WEBHOOK_URL="${FINLEGAL_ALERT_WEBHOOK_URL:-}"
TOKEN="${FINLEGAL_ALERT_WEBHOOK_TOKEN:-}"
TIMEOUT="${FINLEGAL_ALERT_TIMEOUT_SECONDS:-10}"
RETRIES="${FINLEGAL_ALERT_RETRIES:-3}"
DRY_RUN="${FINLEGAL_ALERT_DRY_RUN:-0}"

if [[ -z "$INPUT" || ! -f "$INPUT" ]]; then
  echo "Usage: $0 audit-result.json [deployment-record.json]" >&2
  exit 2
fi
if [[ -n "$RECORD" && ! -f "$RECORD" ]]; then
  echo "ERROR: deployment record does not exist: $RECORD" >&2
  exit 2
fi
command -v jq >/dev/null 2>&1 || { echo "ERROR: jq is required" >&2; exit 2; }
command -v curl >/dev/null 2>&1 || { echo "ERROR: curl is required" >&2; exit 2; }

if ! jq -e . "$INPUT" >/dev/null 2>&1; then
  echo "ERROR: audit input is not valid JSON" >&2
  exit 2
fi

# Critical conditions are explicit: failed checks with CRITICAL severity, or any
# tenant-isolation/residency controls that failed. A generic audit failure alone
# is not promoted to Critical without a Critical result.
CRITICAL_COUNT=$(jq '[.results[]? | select(.status == "FAIL" and (.severity == "CRITICAL" or (.id | test("^R-03[01]$|^R-01[0-7]$|^R-02[0-5]$"))))] | length' "$INPUT")
FAILED_COUNT=$(jq '[.results[]? | select(.status == "FAIL")] | length' "$INPUT")

if [[ "$CRITICAL_COUNT" -eq 0 ]]; then
  echo "No Critical compliance stop condition detected; no notification sent. failed_checks=$FAILED_COUNT"
  exit 0
fi

if [[ -z "$WEBHOOK_URL" && "$DRY_RUN" != "1" ]]; then
  echo "ERROR: Critical stop detected but FINLEGAL_ALERT_WEBHOOK_URL is not configured; failing closed" >&2
  exit 1
fi

NOW_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)
SOURCE="${RECORD:-$INPUT}"
DEPLOYMENT_ID=$(jq -r '.deployment_id // .deploymentId // "unknown"' "$SOURCE")
CUSTOMER_ID=$(jq -r '.customer_id // .customerId // "customer-redacted"' "$SOURCE")
PARTNER=$(jq -r '.gsi_partner // .gsiPartner // "unknown"' "$SOURCE")
REGION=$(jq -r '.residency.customer_region // .region // "unknown"' "$SOURCE")
VERSION=$(jq -r '.artifact.version // "unknown"' "$SOURCE")
SOURCE_SHA=$(jq -r '.artifact.source_sha // "unknown"' "$SOURCE")

# Send only customer-safe metadata and failed-check summaries; never send the
# original audit record, secrets, raw logs, private keys, or customer content.
FAILED_SUMMARY=$(jq -c '[.results[]? | select(.status == "FAIL") | {id,severity,message}]' "$INPUT")
PAYLOAD=$(jq -n \
  --arg event "finlegal.compliance.critical_stop" \
  --arg occurred_at "$NOW_UTC" \
  --arg deployment_id "$DEPLOYMENT_ID" \
  --arg customer_id "$CUSTOMER_ID" \
  --arg partner "$PARTNER" \
  --arg region "$REGION" \
  --arg version "$VERSION" \
  --arg source_sha "$SOURCE_SHA" \
  --argjson failed_checks "$FAILED_SUMMARY" \
  --argjson critical_count "$CRITICAL_COUNT" \
  '{event:$event,occurred_at:$occurred_at,severity:"CRITICAL",deployment_id:$deployment_id,customer_id:$customer_id,gsi_partner:$partner,region:$region,artifact_version:$version,source_sha:$source_sha,critical_count:$critical_count,failed_checks:$failed_checks,action_required:"Pause affected installation, redistribution, processing, and rollout expansion. Preserve evidence and invoke the Critical-stop escalation protocol."}' )

if [[ "$DRY_RUN" == "1" ]]; then
  jq . <<<"$PAYLOAD"
  exit 0
fi

CURL_ARGS=(--fail-with-body --silent --show-error --max-time "$TIMEOUT" -H 'Content-Type: application/json' --data-binary @-)
if [[ -n "$TOKEN" ]]; then
  CURL_ARGS+=( -H "Authorization: Bearer $TOKEN" )
fi

attempt=1
while [[ "$attempt" -le "$RETRIES" ]]; do
  if printf '%s' "$PAYLOAD" | curl "${CURL_ARGS[@]}" "$WEBHOOK_URL" >/dev/null; then
    echo "Critical compliance-stop notification delivered: deployment=$DEPLOYMENT_ID attempt=$attempt"
    exit 0
  fi
  if [[ "$attempt" -lt "$RETRIES" ]]; then
    sleep $((attempt * 2))
  fi
  attempt=$((attempt + 1))
done

echo "ERROR: Critical compliance-stop notification failed after $RETRIES attempts; incident record must be updated manually" >&2
exit 1
