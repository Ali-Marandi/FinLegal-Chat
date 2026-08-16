#!/usr/bin/env bash
set -euo pipefail

# Monitor GitHub Actions runs for the FinLegal v0.2.0 enterprise release branch.
# Requires: gh, jq, authenticated GitHub CLI session.
# Example:
#   ./scripts/monitor-release-workflow.sh --repo Ali-Marandi/FinLegal-Chat --once
#   ./scripts/monitor-release-workflow.sh --repo Ali-Marandi/FinLegal-Chat --interval 30

REPO="Ali-Marandi/FinLegal-Chat"
BRANCH="release/v0.2.0-enterprise"
INTERVAL=30
ONCE=0
SINCE_RUN_ID=""
NOTIFY_COMMAND=""

usage() {
  cat <<'USAGE'
Usage: monitor-release-workflow.sh [options]

Options:
  --repo OWNER/REPO       Repository to monitor.
  --branch BRANCH         Branch to monitor.
  --interval SECONDS      Poll interval; default 30.
  --since-run-id ID       Ignore runs with database IDs at or below ID.
  --notify-command CMD    Run CMD on terminal failure; RUN_ID, STATUS, and URL are exported.
  --once                  Inspect current runs once and exit.
  -h, --help              Show this help.

The monitor returns:
  0 when --once completes without a failed/cancelled run;
  1 when a terminal run is failed, cancelled, timed out, action-required, or has a failed critical job;
  2 for configuration or dependency errors.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo) REPO="${2:?Missing value for --repo}"; shift 2 ;;
    --branch) BRANCH="${2:?Missing value for --branch}"; shift 2 ;;
    --interval) INTERVAL="${2:?Missing value for --interval}"; shift 2 ;;
    --since-run-id) SINCE_RUN_ID="${2:?Missing value for --since-run-id}"; shift 2 ;;
    --notify-command) NOTIFY_COMMAND="${2:?Missing value for --notify-command}"; shift 2 ;;
    --once) ONCE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

command -v gh >/dev/null 2>&1 || { echo 'GitHub CLI (gh) is required.' >&2; exit 2; }
command -v jq >/dev/null 2>&1 || { echo 'jq is required.' >&2; exit 2; }
gh auth status >/dev/null 2>&1 || { echo 'GitHub CLI is not authenticated.' >&2; exit 2; }
[[ "$INTERVAL" =~ ^[0-9]+$ ]] || { echo '--interval must be an integer.' >&2; exit 2; }

log_json() {
  local event="$1" run_id="$2" status="$3" conclusion="$4" url="$5" message="$6"
  jq -cn --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg event "$event" --arg repo "$REPO" --arg branch "$BRANCH" \
    --arg run_id "$run_id" --arg status "$status" --arg conclusion "$conclusion" \
    --arg url "$url" --arg message "$message" \
    '{timestamp:$timestamp,event:$event,repo:$repo,branch:$branch,run_id:$run_id,status:$status,conclusion:$conclusion,url:$url,message:$message}'
}

critical_job_failure() {
  local run_id="$1"
  local jobs
  jobs="$(gh run view "$run_id" --repo "$REPO" --json jobs --jq '.jobs[] | {name,status,conclusion}' 2>/dev/null || true)"
  [[ -n "$jobs" ]] || return 1
  printf '%s\n' "$jobs" | jq -s -e '
    any(.[]; (.name | ascii_downcase | test("windows|macos|publish|attest|provenance|sign")) and (.status == "completed") and (.conclusion != "success"))
  ' >/dev/null
}

handle_terminal_failure() {
  local run_id="$1" status="$2" conclusion="$3" url="$4"
  log_json failure "$run_id" "$status" "$conclusion" "$url" "Terminal workflow failure or release-critical job failure" >&2
  if [[ -n "$NOTIFY_COMMAND" ]]; then
    RUN_ID="$run_id" STATUS="$status" CONCLUSION="$conclusion" RUN_URL="$url" REPO="$REPO" BRANCH="$BRANCH" bash -c "$NOTIFY_COMMAND"
  fi
  return 1
}

last_seen="${SINCE_RUN_ID:-0}"
while true; do
  runs="$(gh run list --repo "$REPO" --branch "$BRANCH" --limit 20 --json databaseId,status,conclusion,workflowName,headSha,createdAt,url 2>/dev/null)" || {
    log_json error "" "unknown" "unknown" "" "Unable to query GitHub Actions runs" >&2
    [[ "$ONCE" -eq 1 ]] && exit 1
    sleep "$INTERVAL"
    continue
  }

  found_new=0
  while IFS= read -r run; do
    [[ -n "$run" ]] || continue
    run_id="$(jq -r '.databaseId' <<< "$run")"
    [[ "$run_id" =~ ^[0-9]+$ ]] || continue
    (( run_id > last_seen )) || continue
    found_new=1
    status="$(jq -r '.status' <<< "$run")"
    conclusion="$(jq -r '.conclusion // ""' <<< "$run")"
    workflow="$(jq -r '.workflowName' <<< "$run")"
    url="$(jq -r '.url' <<< "$run")"
    log_json observed "$run_id" "$status" "$conclusion" "$url" "$workflow"

    if [[ "$status" == "completed" ]]; then
      if [[ "$conclusion" != "success" ]]; then
        handle_terminal_failure "$run_id" "$status" "$conclusion" "$url"
      fi
      if critical_job_failure "$run_id"; then
        handle_terminal_failure "$run_id" "$status" "$conclusion" "$url"
      fi
      log_json passed "$run_id" "$status" "$conclusion" "$url" "Workflow and critical release jobs passed"
    fi
    (( run_id > last_seen )) && last_seen="$run_id"
  done < <(jq -c 'sort_by(.databaseId)[]' <<< "$runs")

  if [[ "$ONCE" -eq 1 ]]; then
    [[ "$found_new" -eq 1 ]] || log_json idle "" "none" "none" "" "No new workflow runs found"
    exit 0
  fi
  sleep "$INTERVAL"
done
