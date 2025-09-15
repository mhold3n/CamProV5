#!/usr/bin/env bash
# gha-repeatable-workflow-test.sh
# Requirements: gh >= 2.0, jq
# Env:
#   OWNER                 GitHub org/user (default: mhold3n)
#   REPO                  GitHub repo (default: CamProV5)
#   REF                   Git ref to dispatch (default: main)
#   WORKFLOWS             Comma-separated workflow file names or IDs. Defaults to:
#                         ci.yml,codeql.yml,dependency-review.yml,files-to-issues.yml,files_to_issues.yml,guard-shared-indexes.yml,issues-downsync.yml,labeler.yml,pr-title-lint.yml,python-ci.yml,python.yml,release-drafter.yml,release.yml,shared-indexes-smoke.yml,todos_to_issues.yml
#                         Example override: "ci.yml,analysis.yml"
#   WORKFLOW_INPUTS       Optional JSON mapping workflow -> inputs object.
#                         Example: '{"ci.yml":{"runFast":"true"},"analysis.yml":{"dataset":"small"}}'
#   TIMEOUT_SECONDS       Optional total poll timeout (default 300)
#   POLL_INTERVAL_SECONDS Optional poll interval (default 5)

set -euo pipefail

if ! command -v gh >/dev/null 2>&1; then
  echo "ERROR: gh CLI is required. https://cli.github.com/" >&2
  exit 1
fi
if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: jq is required. https://stedolan.github.io/jq/" >&2
  exit 1
fi

# Predefined default workflows list based on the repository's .github/workflows directory
DEFAULT_WORKFLOWS="ci.yml,codeql.yml,dependency-review.yml,files-to-issues.yml,files_to_issues.yml,guard-shared-indexes.yml,issues-downsync.yml,labeler.yml,pr-title-lint.yml,python-ci.yml,python.yml,release-drafter.yml,release.yml,shared-indexes-smoke.yml,todos_to_issues.yml"

OWNER="${OWNER:-mhold3n}"
REPO="${REPO:-CamProV5}"
REF="${REF:-main}"
WORKFLOWS="${WORKFLOWS:-$DEFAULT_WORKFLOWS}"
WORKFLOW_INPUTS="${WORKFLOW_INPUTS:-{}}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-300}"
POLL_INTERVAL_SECONDS="${POLL_INTERVAL_SECONDS:-5}"
AUTO_ENABLE_WORKFLOWS="${AUTO_ENABLE_WORKFLOWS:-true}"
VERBOSE="${VERBOSE:-false}"
DEBUG="${DEBUG:-false}"

# Helper function for verbose output
log_verbose() {
  [[ "$VERBOSE" == "true" ]] && echo "   [VERBOSE] $*" >&2
}

log_debug() {
  [[ "$DEBUG" == "true" ]] && echo "   [DEBUG] $*" >&2
}

# Helper function to detect rate limiting and implement backoff
detect_rate_limit_and_backoff() {
  local api_output="$1"
  local attempt="$2"
  
  # Check if output contains rate limit indicators
  if echo "$api_output" | grep -qi "rate limit\|403\|too many requests\|x-ratelimit"; then
    local backoff_seconds=$((attempt * attempt * 5))  # Quadratic backoff: 5, 20, 45, 80, 125...
    local max_backoff=300  # 5 minutes max
    
    if [[ $backoff_seconds -gt $max_backoff ]]; then
      backoff_seconds=$max_backoff
    fi
    
    log_debug "Rate limit detected, backing off for ${backoff_seconds}s (attempt $attempt)"
    echo "   -> Rate limiting detected, waiting ${backoff_seconds}s before retry..."
    sleep "$backoff_seconds"
    return 0  # Rate limit detected
  fi
  
  return 1  # No rate limit detected
}

# Enhanced API call wrapper with rate limit detection
safe_gh_api() {
  local endpoint="$1"
  shift  # Remove first argument, rest are gh api parameters
  local attempt=1
  local max_attempts=3  # Reduced from 5 to prevent long hangs
  local timeout_seconds=10  # Add timeout for individual API calls
  
  while [[ $attempt -le $max_attempts ]]; do
    local output
    local exit_code=0
    
    log_debug "safe_gh_api: attempt $attempt/$max_attempts for $endpoint"
    
    # Use timeout to prevent hanging on individual calls
    if command -v timeout >/dev/null 2>&1; then
      output="$(timeout $timeout_seconds gh api "$endpoint" "$@" 2>&1)" || exit_code=$?
    else
      # Fallback for systems without timeout command
      output="$(gh api "$endpoint" "$@" 2>&1)" || exit_code=$?
    fi
    
    # Check if output is valid JSON (not HTML error page)
    if [[ $exit_code -eq 0 ]] && echo "$output" | jq . >/dev/null 2>&1; then
      log_debug "safe_gh_api: success on attempt $attempt for $endpoint"
      echo "$output"
      return 0
    fi
    
    log_debug "safe_gh_api: API call failed (exit_code=$exit_code) on attempt $attempt: $(echo "$output" | head -c 100)..."
    
    # Check for timeout
    if [[ $exit_code -eq 124 ]] || echo "$output" | grep -qi "timeout"; then
      log_debug "Timeout detected on attempt $attempt"
      attempt=$((attempt + 1))
      continue
    fi
    
    # Check for HTML error responses (GitHub returns HTML during API issues)
    if echo "$output" | grep -qi "<html>\|<!DOCTYPE\|<body>\|<head>"; then
      log_debug "HTML error page detected instead of JSON API response (attempt $attempt)"
      attempt=$((attempt + 1))
      sleep 2  # Shorter delay to prevent hangs
      continue
    fi
    
    # Check for rate limiting (but don't use the potentially hanging detect_rate_limit_and_backoff)
    if echo "$output" | grep -qi "rate limit\|403\|too many requests\|x-ratelimit"; then
      log_debug "Rate limit detected on attempt $attempt"
      attempt=$((attempt + 1))
      sleep $((attempt * 2))  # Simple backoff
      continue
    fi
    
    # Check for JSON parsing errors (often caused by HTML responses)
    if echo "$output" | grep -qi "parse error\|invalid.*json\|unexpected token"; then
      log_debug "JSON parsing error detected, likely HTML response (attempt $attempt)"
      attempt=$((attempt + 1))
      sleep 2
      continue
    fi
    
    # For any other error, don't retry endlessly
    log_debug "Non-retryable error or max attempts reached for $endpoint"
    break
  done
  
  # All attempts failed, return empty string to trigger fallback to cached data
  log_debug "safe_gh_api: all attempts failed for $endpoint, returning empty"
  echo ""
  return 1
}

if [[ -z "$OWNER" || -z "$REPO" || -z "$REF" ]]; then
  echo "Usage: OWNER=... REPO=... REF=... [WORKFLOWS='file.yml,file2.yml'] $0" >&2
  exit 1
fi

repo_slug="$OWNER/$REPO"

# Inform if using the default workflows list (when WORKFLOWS env var was not provided)
if [[ "$WORKFLOWS" == "$DEFAULT_WORKFLOWS" ]]; then
  echo "WORKFLOWS not provided; using default workflows list:"
  echo "  $DEFAULT_WORKFLOWS"
fi

# Helper: get epoch seconds
now_epoch() {
  date -u +"%s"
}

# Helper: RFC3339 timestamp
now_rfc3339() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

start_ts="$(now_rfc3339)"
deadline="$(( $(now_epoch) + TIMEOUT_SECONDS ))"

# Optional: Map workflow file names/IDs to your WorkflowType classification.
# Adjust this mapping as needed for your project.
get_workflow_type() {
  local wf="$1"
  case "$wf" in
    *design*|*Design*) echo "DESIGN_WORKFLOW" ;;
    *analysis*|*Analysis*) echo "ANALYSIS_WORKFLOW" ;;
    *simul*|*Simul*|*simulation*) echo "SIMULATION_WORKFLOW" ;;
    *report*|*Report*) echo "REPORTING_WORKFLOW" ;;
    *collab*|*Collab*) echo "COLLABORATION_WORKFLOW" ;;
    *) echo "GENERAL_WORKFLOW" ;;
  esac
}

# Resolve workflow path from id or filename
resolve_workflow_path() {
  local wf="$1"
  # Try GitHub API to resolve path (works for numeric id or filename)
  local path
  if path="$(gh api "repos/$repo_slug/actions/workflows/$wf" -q .path 2>/dev/null)"; then
    echo "$path"
    return 0
  fi
  # Fallback: assume filename under standard workflows dir
  if [[ "$wf" == *.yml || "$wf" == *.yaml ]]; then
    echo ".github/workflows/$wf"
    return 0
  fi
  return 1
}

# Check if a workflow file supports manual dispatch by scanning YAML for 'workflow_dispatch:'
supports_manual_dispatch() {
  local wf="$1"
  local path
  if ! path="$(resolve_workflow_path "$wf")"; then
    return 2  # unknown (cannot resolve path)
  fi
  # Fetch raw YAML content at the ref without base64 decoding hassles
  local yaml
  if ! yaml="$(gh api -H "Accept: application/vnd.github.raw" "repos/$repo_slug/contents/$path?ref=$REF" 2>/dev/null)"; then
    return 2  # unknown (cannot read content)
  fi
  if echo "$yaml" | grep -qE '(^|[[:space:]])workflow_dispatch:'; then
    return 0
  else
    return 1
  fi
}

# Trigger dispatch for each workflow and collect pending records
IFS=',' read -r -a WF_ARRAY <<< "$WORKFLOWS"
declare -A RUN_RECORD_JSON       # workflow -> JSON with workflow, type, dispatch_status, run_id, etc.
declare -A WORKFLOW_TO_RUN_ID    # workflow -> run_id (once discovered)
declare -A WORKFLOW_LIST_HANDLE  # workflow -> listing handle (numeric id if resolved, else filename)

echo "Dispatching workflows on $repo_slug at ref '$REF'..."
for WF in "${WF_ARRAY[@]}"; do
  WF_TRIMMED="$(echo "$WF" | xargs)"
  if [[ -z "$WF_TRIMMED" ]]; then continue; fi

  # Extract inputs for this workflow if present
  INPUTS_FOR_WF="$(echo "$WORKFLOW_INPUTS" | jq -c --arg wf "$WF_TRIMMED" '.[$wf] // {}')"

  echo " - Dispatching: $WF_TRIMMED with inputs: $INPUTS_FOR_WF"

  # Pre-check: does this workflow support manual dispatch?
  precheck_result=2
  if supports_manual_dispatch "$WF_TRIMMED"; then
    precheck_result=0
    echo "   -> Pre-check: workflow_dispatch present"
  else
    precheck_result=$?
    if [[ "$precheck_result" -eq 1 ]]; then
      echo "   -> Pre-check: workflow_dispatch NOT present (skipping dispatch)"
      WF_TYPE="$(get_workflow_type "$WF_TRIMMED")"
      RUN_RECORD_JSON["$WF_TRIMMED"]="$(jq -c -n --arg wf "$WF_TRIMMED" --arg wft "$WF_TYPE" --arg st "dispatch_failed" --arg msg "no_workflow_dispatch" \
        '{workflow:$wf, type:$wft, dispatch_status:$st, status:"not_started", conclusion:"unknown", error_reason:$msg}')"
      continue
    else
      echo "   -> Pre-check: unable to determine support (proceeding to attempt dispatch)"
    fi
  fi

  # Resolve workflow id and state, store listing handle; check state
  WF_META="$(gh api "repos/$repo_slug/actions/workflows/$WF_TRIMMED" 2>/dev/null || true)"
  WF_ID=""
  WF_STATE=""
  if [[ -n "$WF_META" ]]; then
    WF_ID="$(echo "$WF_META" | jq -r '.id // empty')"
    WF_STATE="$(echo "$WF_META" | jq -r '.state // empty')"
  fi
  WF_LIST_HANDLE="${WF_ID:-$WF_TRIMMED}"
  WORKFLOW_LIST_HANDLE["$WF_TRIMMED"]="$WF_LIST_HANDLE"

  # Add comprehensive workflow diagnostics in verbose/debug mode
  if [[ "$VERBOSE" == "true" || "$DEBUG" == "true" ]]; then
    echo "   -> Workflow diagnostics:"
    echo "      ID: ${WF_ID:-'not found'}"
    echo "      State: ${WF_STATE:-'unknown'}"
    echo "      List handle: $WF_LIST_HANDLE"
    
    # Check if workflow exists in target ref
    if [[ -n "$WF_ID" ]]; then
      WF_RUNS_COUNT="$(gh api "repos/$repo_slug/actions/workflows/$WF_ID/runs?per_page=1" -q '.total_count' 2>/dev/null || echo 0)"
      echo "      Previous runs: $WF_RUNS_COUNT"
    fi
    
    # Check branch/ref existence
    BRANCH_EXISTS="$(gh api "repos/$repo_slug/branches/$REF" -q '.name' 2>/dev/null || echo 'not found')"
    echo "      Target ref '$REF': $BRANCH_EXISTS"
  fi

  if [[ -n "$WF_STATE" && "$WF_STATE" != "active" ]]; then
    if [[ "$AUTO_ENABLE_WORKFLOWS" == "true" && -n "$WF_ID" && ( "$WF_STATE" == "disabled_inactivity" || "$WF_STATE" == "disabled_manually" ) ]]; then
      echo "   -> Workflow state is '$WF_STATE'; attempting to enable via API..."
      if gh api -X PUT "repos/$repo_slug/actions/workflows/$WF_ID/enable" -i >/dev/null 2>&1; then
        # Re-fetch state to verify
        WF_STATE="$(gh api "repos/$repo_slug/actions/workflows/$WF_TRIMMED" -q .state 2>/dev/null || echo "")"
        if [[ "$WF_STATE" == "active" ]]; then
          echo "   -> Workflow enabled successfully; proceeding to dispatch."
        else
          echo "   -> Enable attempt did not set state to active (state='$WF_STATE'). Skipping dispatch."
          WF_TYPE="$(get_workflow_type "$WF_TRIMMED")"
          RUN_RECORD_JSON["$WF_TRIMMED"]="$(jq -c -n --arg wf "$WF_TRIMMED" --arg wft "$WF_TYPE" --arg st "dispatch_failed" --arg msg "state_$WF_STATE" '{workflow:$wf, type:$wft, dispatch_status:$st, status:"not_started", conclusion:"unknown", error_reason:$msg}')"
          continue
        fi
      else
        echo "   -> Enable attempt failed. Skipping dispatch."
        WF_TYPE="$(get_workflow_type "$WF_TRIMMED")"
        RUN_RECORD_JSON["$WF_TRIMMED"]="$(jq -c -n --arg wf "$WF_TRIMMED" --arg wft "$WF_TYPE" --arg st "dispatch_failed" --arg msg "enable_failed_$WF_STATE" '{workflow:$wf, type:$wft, dispatch_status:$st, status:"not_started", conclusion:"unknown", error_reason:$msg}')"
        continue
      fi
    else
      echo "   -> Workflow state is '$WF_STATE' (needs enabling or not present on ref '$REF'). Skipping dispatch."
      WF_TYPE="$(get_workflow_type "$WF_TRIMMED")"
      RUN_RECORD_JSON["$WF_TRIMMED"]="$(jq -c -n --arg wf "$WF_TRIMMED" --arg wft "$WF_TYPE" --arg st "dispatch_failed" --arg msg "state_$WF_STATE" '{workflow:$wf, type:$wft, dispatch_status:$st, status:"not_started", conclusion:"unknown", error_reason:$msg}')"
      continue
    fi
  fi

  # Attempt dispatch (capture error details for better diagnostics)
  DISPATCH_OK=true
  DISPATCH_OUTPUT=""
  if [[ "$INPUTS_FOR_WF" == "{}" ]]; then
    # No inputs: omit the field entirely
    DISPATCH_OUTPUT="$(gh api -X POST "repos/$repo_slug/actions/workflows/$WF_TRIMMED/dispatches" \
          -H "Accept: application/vnd.github+json" \
          -f "ref=$REF" -i 2>&1)" || DISPATCH_OK=false
  else
    # Non-empty inputs: pass raw JSON object via -F
    DISPATCH_OUTPUT="$(gh api -X POST "repos/$repo_slug/actions/workflows/$WF_TRIMMED/dispatches" \
          -H "Accept: application/vnd.github+json" \
          -f "ref=$REF" \
          -F "inputs=$INPUTS_FOR_WF" -i 2>&1)" || DISPATCH_OK=false
  fi

  WF_TYPE="$(get_workflow_type "$WF_TRIMMED")"

  if [[ "$DISPATCH_OK" = false ]]; then
    echo "   -> Dispatch FAILED for $WF_TRIMMED"
    echo "   -> Error details: $DISPATCH_OUTPUT"
    echo "   -> Checking workflow existence and state..."
    
    # Try to get more details about why dispatch failed
    if [[ -n "$WF_ID" ]]; then
      WF_DETAILED="$(gh api "repos/$repo_slug/actions/workflows/$WF_ID" 2>&1 || echo "API call failed")"
      echo "   -> Workflow details: $WF_DETAILED"
    else
      echo "   -> Workflow ID not resolved, may not exist in .github/workflows/"
    fi
    
    # Store error details in the record
    RUN_RECORD_JSON["$WF_TRIMMED"]="$(jq -c -n --arg wf "$WF_TRIMMED" --arg wft "$WF_TYPE" --arg st "dispatch_failed" --arg err "$DISPATCH_OUTPUT" \
      '{workflow:$wf, type:$wft, dispatch_status:$st, status:"not_started", conclusion:"unknown", error_details:$err}')"
    continue
  fi

  # After successful dispatch, add this verification
  if [[ "$DISPATCH_OK" = true ]]; then
    # Wait a moment for the run to be created
    sleep 2
    
    # Quick verification that dispatch actually triggered a run
    if [[ -n "$WF_ID" ]]; then
      RECENT_RUN_CHECK="$(gh api "repos/$repo_slug/actions/workflows/$WF_ID/runs?per_page=1" \
          -q '.workflow_runs[0].created_at // empty' 2>/dev/null)"
      
      if [[ -n "$RECENT_RUN_CHECK" ]]; then
        # Parse timestamp to check if it's very recent (within 30 seconds)
        RECENT_EPOCH="$(date -j -f '%Y-%m-%dT%H:%M:%SZ' "$RECENT_RUN_CHECK" '+%s' 2>/dev/null || echo 0)"
        DISPATCH_EPOCH="$(date -j -f '%Y-%m-%dT%H:%M:%SZ' "$start_ts" '+%s' 2>/dev/null || echo 0)"
        
        if [[ $((RECENT_EPOCH - DISPATCH_EPOCH)) -lt 30 ]]; then
          log_debug "Confirmed recent run creation for $WF_TRIMMED"
        fi
      fi
    fi
  fi

  # Add after successful dispatch
  DISPATCH_TIMESTAMP="$(now_rfc3339)"
  
  # Store initial record; run_id will be resolved in polling
  RUN_RECORD_JSON["$WF_TRIMMED"]="$(jq -c -n \
    --arg wf "$WF_TRIMMED" \
    --arg wft "$WF_TYPE" \
    --arg dispatch_ts "$DISPATCH_TIMESTAMP" \
    '{workflow:$wf, type:$wft, dispatch_status:"ok", status:"dispatched", conclusion:"unknown", dispatch_time:$dispatch_ts}')"

done

# Cache working API data for fallback during polling failures
declare -A CACHED_RUNS_DATA  # workflow_id -> runs JSON data
CACHED_REPO_RUNS=""  # Repository-wide runs data

# Add debug section with repository diagnostics and cache working data
if [[ "$DEBUG" == "true" ]]; then
  echo
  echo "=== DEBUG: Repository and workflow diagnostics ==="
  
  # Check repository permissions
  echo "Repository permissions:"
  gh api "repos/$repo_slug" -q '{permissions: .permissions, private: .private}' 2>/dev/null || echo "Cannot access repo metadata"
  
  # List all workflows with their states
  echo "All workflows in repository:"
  gh api "repos/$repo_slug/actions/workflows" -q '.workflows[] | "\(.name): \(.state) (ID: \(.id))"' 2>/dev/null
  
  # Check recent workflow runs and cache the data
  echo "Recent workflow runs:"
  CACHED_REPO_RUNS="$(safe_gh_api "repos/$repo_slug/actions/runs?per_page=50" 2>/dev/null || echo '')"
  if [[ -n "$CACHED_REPO_RUNS" ]]; then
    # Verify the cached data is valid JSON before trying to parse it
    if echo "$CACHED_REPO_RUNS" | jq . >/dev/null 2>&1; then
      echo "$CACHED_REPO_RUNS" | jq -r '.workflow_runs[] | "\(.workflow_id): \(.status)/\(.conclusion) (\(.created_at))"' 2>/dev/null || echo "Error parsing cached runs"
      log_debug "Cached $(echo "$CACHED_REPO_RUNS" | jq '.workflow_runs | length' 2>/dev/null || echo 'unknown') runs for fallback"
    else
      echo "Cached repository runs data is not valid JSON, clearing cache"
      log_debug "Invalid JSON in CACHED_REPO_RUNS: $(echo "$CACHED_REPO_RUNS" | head -c 200)..."
      CACHED_REPO_RUNS=""
    fi
  else
    echo "Failed to cache repository runs data"
  fi
  echo
fi

# Always try to cache runs data (even without DEBUG mode) for polling fallback
if [[ -z "$CACHED_REPO_RUNS" ]]; then
  log_debug "Caching repository runs data for polling fallback..."
  CACHED_REPO_RUNS="$(safe_gh_api "repos/$repo_slug/actions/runs?per_page=100" 2>/dev/null || echo '')"
  if [[ -n "$CACHED_REPO_RUNS" ]]; then
    log_debug "Successfully cached $(echo "$CACHED_REPO_RUNS" | jq '.workflow_runs | length' 2>/dev/null || echo 'unknown') runs"
  else
    log_debug "Failed to cache repository runs data - live API calls may be unreliable"
  fi
fi

# Cache individual workflow runs data for workflows we're testing
for WF in "${WF_ARRAY[@]}"; do
  WF_TRIMMED="$(echo "$WF" | xargs)"
  if [[ -z "$WF_TRIMMED" ]]; then continue; fi
  
  # Skip if dispatch failed
  if [[ -z "${RUN_RECORD_JSON[$WF_TRIMMED]}" ]]; then continue; fi
  dispatch_status="$(echo "${RUN_RECORD_JSON[$WF_TRIMMED]}" | jq -r '.dispatch_status // "unknown"')"
  if [[ "$dispatch_status" != "ok" ]]; then continue; fi
  
  # Cache workflow-specific runs data
  WF_HANDLE="${WORKFLOW_LIST_HANDLE[$WF_TRIMMED]:-$WF_TRIMMED}"
  if [[ -n "$WF_HANDLE" ]]; then
    CACHED_WF_RUNS="$(safe_gh_api "repos/$repo_slug/actions/workflows/$WF_HANDLE/runs?per_page=20" 2>/dev/null || echo '')"
    if [[ -n "$CACHED_WF_RUNS" ]]; then
      CACHED_RUNS_DATA["$WF_HANDLE"]="$CACHED_WF_RUNS"
      log_debug "Cached workflow-specific runs for $WF_TRIMMED (handle: $WF_HANDLE)"
    fi
  fi
done

# Polling loop
echo "Polling workflow runs (timeout=${TIMEOUT_SECONDS}s, interval=${POLL_INTERVAL_SECONDS}s)..."

# Add this helper function
is_run_recent_enough() {
  local run_created_at="$1"
  local dispatch_time="$2"
  local max_delay_seconds=300  # 5 minutes max reasonable delay
  
  if ! command -v python3 >/dev/null 2>&1; then
    return 0  # If no python, assume it's recent enough
  fi
  
  python3 - <<PY
import sys
from datetime import datetime, timezone, timedelta

try:
    run_time = datetime.strptime('$run_created_at', '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    dispatch_time = datetime.strptime('$dispatch_time', '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    
    # Run should be after dispatch but within reasonable delay
    if run_time >= dispatch_time and (run_time - dispatch_time).total_seconds() <= $max_delay_seconds:
        sys.exit(0)  # Recent enough
    else:
        sys.exit(1)  # Too old or in future
except Exception as e:
    sys.exit(0)  # On error, assume it's valid
PY
}

find_run_id_for_workflow() {
  local wf="$1"
  local handle="${WORKFLOW_LIST_HANDLE[$wf]:-$wf}"
  local attempt=1
  local max_attempts=12  # Up to 60 seconds of retries
  local base_delay=1
  
  while [[ $attempt -le $max_attempts ]]; do
    local runs=""
    local run_id=""
    local using_cache=false
    
    # Strategy 1: Try repository-wide runs first (more reliable)
    if [[ "$handle" =~ ^[0-9]+$ ]]; then
      local repo_runs
      repo_runs="$(safe_gh_api "repos/$repo_slug/actions/runs" \
          -H "Accept: application/vnd.github+json" \
          -f "per_page=50" 2>/dev/null || echo '')"
      
      # Check if API call failed (empty result) and use cached data as fallback
      if [[ -z "$repo_runs" ]] && [[ -n "$CACHED_REPO_RUNS" ]]; then
        repo_runs="$CACHED_REPO_RUNS"
        using_cache=true
        log_debug "Live API failed, using cached repository runs data for $wf"
      elif [[ -z "$repo_runs" ]]; then
        log_debug "Live API failed and no cached repository data available for $wf"
      fi
      
      # Debug the repo-wide API call
      if [[ "$DEBUG" == "true" ]]; then
        if [[ -n "$repo_runs" ]]; then
          local runs_count="$(echo "$repo_runs" | jq '.workflow_runs | length' 2>/dev/null || echo 'error')"
          echo "   [DEBUG] Repository-wide API returned $runs_count runs (cached: $using_cache)" >&2
          log_debug "Using repository-wide runs strategy for $wf"
        else
          echo "   [DEBUG] Repository-wide API call failed and no cached data available" >&2
          # Try to see what went wrong
          REPO_API_ERROR="$(safe_gh_api "repos/$repo_slug/actions/runs" \
              -H "Accept: application/vnd.github+json" \
              -f "per_page=50" 2>&1 || echo "Repo API call failed")"
          echo "   [DEBUG] Repo API error: $REPO_API_ERROR" >&2
        fi
      fi
      
      if [[ -n "$repo_runs" ]]; then
        runs="$repo_runs"
      fi
    fi
    
    # Strategy 2: Fallback to workflow-specific endpoint if repo-wide failed
    if [[ -z "$runs" ]]; then
      runs="$(safe_gh_api "repos/$repo_slug/actions/workflows/$handle/runs" \
          -H "Accept: application/vnd.github+json" \
          -f "per_page=20" 2>/dev/null || echo "")"
      
      # Check if API call failed (empty result) and use cached workflow-specific data as fallback
      # Use :- syntax to provide empty string default if array key doesn't exist (prevents unbound variable error)
      if [[ -z "$runs" ]] && [[ -n "${CACHED_RUNS_DATA[$handle]:-}" ]]; then
        runs="${CACHED_RUNS_DATA[$handle]}"
        using_cache=true
        log_debug "Live workflow API failed, using cached workflow runs data for $wf"
      elif [[ -z "$runs" ]]; then
        log_debug "Live workflow API failed and no cached workflow data available for $wf (handle: $handle)"
      fi
      
      # Debug the API call
      if [[ "$DEBUG" == "true" ]]; then
        if [[ -n "$runs" ]]; then
          local runs_count="$(echo "$runs" | jq '.workflow_runs | length' 2>/dev/null || echo 'error')"
          echo "   [DEBUG] Workflow-specific API returned $runs_count runs (cached: $using_cache)" >&2
        else
          echo "   [DEBUG] Workflow-specific API failed and no cached data available" >&2
        fi
      fi
    fi
    
    # Strategy 3: If both live APIs failed, try cached repo data even for non-numeric handles
    if [[ -z "$runs" && -n "$CACHED_REPO_RUNS" ]]; then
      runs="$CACHED_REPO_RUNS"
      using_cache=true
      log_debug "Both live APIs failed, falling back to cached repository data for $wf"
    fi
    
    # Dynamic cushion: start with no cushion, gradually increase
    local cushion_seconds=$(( (attempt - 1) * 30 ))
    local cushion_ts="$start_ts"
    
    if [[ $cushion_seconds -gt 0 ]] && command -v python3 >/dev/null 2>&1; then
      cushion_ts="$(START_TS="$start_ts" CUSHION="$cushion_seconds" python3 - <<'PY'
import os
from datetime import datetime, timezone, timedelta
s = os.environ.get('START_TS') or ''
cushion = int(os.environ.get('CUSHION', '0'))
try:
    dt = datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ')
    dt = (dt - timedelta(seconds=cushion)).replace(tzinfo=timezone.utc)
    print(dt.strftime('%Y-%m-%dT%H:%M:%SZ'))
except Exception:
    print(s)
PY
)"
    fi
    
    # Look for recent runs - filter by workflow_id if using repo-wide data
    if [[ "$handle" =~ ^[0-9]+$ ]] && echo "$runs" | jq -e '.workflow_runs[0].workflow_id' >/dev/null 2>&1; then
      # Repository-wide data - filter by workflow_id
      run_id="$(echo "$runs" | jq -r --argjson wf_id "$handle" --arg since "$cushion_ts" '
        .workflow_runs
        | map(select(.workflow_id == $wf_id and .created_at >= $since))
        | sort_by(.created_at) | reverse
        | .[0].id // empty
      ')"
    else
      # Workflow-specific data - no workflow_id filtering needed
      run_id="$(echo "$runs" | jq -r --arg since "$cushion_ts" '
        .workflow_runs
        | map(select(.created_at >= $since))
        | sort_by(.created_at) | reverse
        | .[0].id // empty
      ')"
    fi
    
    # Enhanced debug logging to understand what's happening
    if [[ "$DEBUG" == "true" ]]; then
      echo "   [DEBUG] Cushion timestamp: $cushion_ts" >&2
      echo "   [DEBUG] Raw runs response length: $(echo "$runs" | jq '.workflow_runs | length' 2>/dev/null || echo 'error')" >&2
      echo "   [DEBUG] Recent runs found: $(echo "$runs" | jq -r --arg since "$cushion_ts" '.workflow_runs | map(select(.created_at >= $since)) | length' 2>/dev/null || echo 'error')" >&2
      if [[ -n "$(echo "$runs" | jq '.workflow_runs[0]' 2>/dev/null)" ]]; then
        echo "   [DEBUG] Most recent run: $(echo "$runs" | jq -c '.workflow_runs[0] | {id, created_at, status}' 2>/dev/null)" >&2
      fi
    fi
    
    if [[ -n "$run_id" ]]; then
      log_debug "Found run_id=$run_id for $wf after $attempt attempts"
      echo "$run_id"
      return 0
    fi
    
    # Fallback: check repo-wide runs if handle is numeric
    if [[ "$handle" =~ ^[0-9]+$ ]]; then
      local repo_runs
      repo_runs="$(gh api "repos/$repo_slug/actions/runs" \
          -H "Accept: application/vnd.github+json" \
          -f "per_page=50" 2>/dev/null || echo '')"
      run_id="$(echo "$repo_runs" | jq -r --argjson wf_id "$handle" --arg since "$cushion_ts" '
        .workflow_runs
        | map(select(.workflow_id == $wf_id and .created_at >= $since))
        | sort_by(.created_at) | reverse
        | .[0].id // empty
      ')"
      
      if [[ -n "$run_id" ]]; then
        log_debug "Found run_id=$run_id via repo-wide search after $attempt attempts"
        echo "$run_id"
        return 0
      fi
    fi
    
    log_debug "Attempt $attempt/$max_attempts failed for $wf (cushion: ${cushion_seconds}s)"
    
    # Progressive delay: 1s, 2s, 4s, 8s, then 5s intervals
    if [[ $attempt -le 4 ]]; then
      sleep $((base_delay * (2 ** (attempt - 1))))
    else
      sleep 5
    fi
    
    attempt=$((attempt + 1))
  done
  
  echo ""  # Return empty if all attempts failed
}

get_run_status() {
  local run_id="$1"
  gh api "repos/$repo_slug/actions/runs/$run_id" \
    -H "Accept: application/vnd.github+json" \
    | jq -c '{status, conclusion, html_url, created_at, updated_at, run_number}'
}

get_run_jobs() {
  local run_id="$1"
  gh api "repos/$repo_slug/actions/runs/$run_id/jobs?per_page=100" \
    -H "Accept: application/vnd.github+json"
}

resolve_failure_point() {
  # Input: jobs JSON
  # Output: compact JSON { job_name, step_name }
  jq -c '
    .jobs as $jobs
    | ($jobs[] | select(.conclusion=="failure") | {job_name:.name, step: (.steps[]? | select(.conclusion=="failure") | .name)}) as $fail
    | if $fail then {job_name:$fail.job_name, step_name:($fail.step // "unknown")} else
        # If no failing conclusion, pick first job with failing step (some runs mark job as cancelled)
        ( $jobs[]? as $j
          | ($j.steps // [])
          | map(select(.conclusion=="failure")) | first
          | if . then {job_name:$j.name, step_name:.name} else empty end
        ) // {}
      end
  '
}

resolve_last_operation_point() {
  # Input: jobs JSON
  # Output: compact JSON { job_name, step_name }
  jq -c '
    .jobs as $jobs
    | (
        $jobs[]? as $j
        | ($j.steps // [])
        | sort_by(.started_at // "0000-00-00T00:00:00Z")
        | last
        | {job_name:$j.name, step_name:(.name // "unknown"), step_status:(.status // "unknown"), step_conclusion:(.conclusion // "unknown")}
      ) // {}
  '
}

all_done=false
while [[ "$(now_epoch)" -lt "$deadline" ]]; do
  pending=0

  for WF in "${WF_ARRAY[@]}"; do
    WF_TRIMMED="$(echo "$WF" | xargs)"
    [[ -z "$WF_TRIMMED" ]] && continue

    rec="${RUN_RECORD_JSON[$WF_TRIMMED]:-}"
    # Skip if dispatch failed
    if [[ -n "$rec" && "$(echo "$rec" | jq -r '.dispatch_status')" == "dispatch_failed" ]]; then
      continue
    fi

    run_id="${WORKFLOW_TO_RUN_ID[$WF_TRIMMED]:-}"
    if [[ -z "$run_id" ]]; then
      log_debug "Attempting to find run_id for $WF_TRIMMED..."
      run_id="$(find_run_id_for_workflow "$WF_TRIMMED" || true)"
      if [[ -n "$run_id" ]]; then
        WORKFLOW_TO_RUN_ID["$WF_TRIMMED"]="$run_id"
        rec="$(echo "${rec:-{}}" | jq -c --arg rid "$run_id" '. + {run_id:($rid|tonumber)}')"
        RUN_RECORD_JSON["$WF_TRIMMED"]="$rec"
        echo "   -> Discovered run_id=$run_id for $WF_TRIMMED"
        log_debug "Successfully found run_id=$run_id for $WF_TRIMMED"
      else
        # still queued/not visible
        log_debug "No run_id found for $WF_TRIMMED, remaining pending"
        pending=$((pending+1))
        continue
      fi
    fi

    # Fetch status for this run
    status_json="$(get_run_status "$run_id")"
    status="$(echo "$status_json" | jq -r '.status')"
    conclusion="$(echo "$status_json" | jq -r '.conclusion // "unknown"')"

    rec="$(echo "$rec" | jq -c --arg s "$status" --arg c "$conclusion" '. + {status:$s, conclusion:$c}')"
    RUN_RECORD_JSON["$WF_TRIMMED"]="$rec"

    if [[ "$status" == "completed" ]]; then
      :
    else
      pending=$((pending+1))
    fi
  done

  if [[ "$pending" -eq 0 ]]; then
    all_done=true
    break
  fi

  sleep "$POLL_INTERVAL_SECONDS"
done

echo
echo "Collecting results..."
echo

# Final reporting
# For each workflow:
# - If status != completed after timeout: mark as timed_out and extract last operation point from jobs
# - If completed with failure: extract failure point
# - Else report conclusion
for WF in "${WF_ARRAY[@]}"; do
  WF_TRIMMED="$(echo "$WF" | xargs)"
  [[ -z "$WF_TRIMMED" ]] && continue

  rec="${RUN_RECORD_JSON[$WF_TRIMMED]:-}"
  [[ -z "$rec" ]] && continue

  dispatch_status="$(echo "$rec" | jq -r '.dispatch_status')"
  wf_type="$(echo "$rec" | jq -r '.type')"
  run_id="$(echo "$rec" | jq -r '.run_id // empty')"
  status="$(echo "$rec" | jq -r '.status')"
  conclusion="$(echo "$rec" | jq -r '.conclusion')"

  echo "=== Workflow: $WF_TRIMMED (type=$wf_type) ==="

  if [[ "$dispatch_status" == "dispatch_failed" ]]; then
    echo "Result: DISPATCH_FAILED"
    error_reason="$(echo "$rec" | jq -r '.error_reason // "unknown"')"
    error_details="$(echo "$rec" | jq -r '.error_details // "none"')"
    echo "Error reason: $error_reason"
    if [[ "$error_details" != "none" ]]; then
      echo "Error details:"
      echo "$error_details" | sed 's/^/  /'
    fi
    echo
    continue
  fi

  if [[ -z "$run_id" ]]; then
    echo "Result: TIMED_OUT (no run appeared)"
    echo "Detail: No run_id discovered since $start_ts"
    echo
    continue
  fi

  # Fetch jobs to resolve last/failure points if needed
  jobs_json="$(get_run_jobs "$run_id")"

  if [[ "$status" != "completed" ]]; then
    # timed out in polling window
    last_point="$(echo "$jobs_json" | resolve_last_operation_point)"
    echo "Result: TIMED_OUT"
    echo "Last operation point: $(echo "$last_point" | jq -r '.job_name // "unknown") / $(echo "$last_point" | jq -r '.step_name // "unknown")"
    echo "Run URL: $(gh api "repos/$repo_slug/actions/runs/$run_id" -q '.html_url')"
    echo
    continue
  fi

  case "$conclusion" in
    success)
      echo "Result: SUCCESS"
      ;;
    failure)
      fail_point="$(echo "$jobs_json" | resolve_failure_point)"
      fp_job="$(echo "$fail_point" | jq -r '.job_name // "unknown"')"
      fp_step="$(echo "$fail_point" | jq -r '.step_name // "unknown"')"
      echo "Result: FAILURE"
      echo "Failure point: $fp_job / $fp_step"
      
      # Get detailed step logs if available
      if [[ "$VERBOSE" == "true" && -n "$run_id" ]]; then
        echo "Job details:"
        echo "$jobs_json" | jq -r '.jobs[] | select(.conclusion=="failure") | "  Job: \(.name) (\(.conclusion))\n  Started: \(.started_at)\n  Completed: \(.completed_at)"'
        
        echo "Failed steps:"
        echo "$jobs_json" | jq -r '.jobs[].steps[]? | select(.conclusion=="failure") | "  Step: \(.name)\n  Conclusion: \(.conclusion)\n  Started: \(.started_at // "unknown")\n  Completed: \(.completed_at // "unknown")"'
      fi
      ;;
    cancelled)
      echo "Result: CANCELLED"
      ;;
    timed_out)
      last_point="$(echo "$jobs_json" | resolve_last_operation_point)"
      echo "Result: TIMED_OUT (run-level)"
      echo "Last operation point: $(echo "$last_point" | jq -r '.job_name // "unknown") / $(echo "$last_point" | jq -r '.step_name // "unknown")"
      ;;
    neutral|skipped|action_required|stale)
      echo "Result: $conclusion"
      ;;
    *)
      echo "Result: UNKNOWN (conclusion=$conclusion)"
      ;;
  esac

  echo "Run URL: $(gh api "repos/$repo_slug/actions/runs/$run_id" -q '.html_url')"
  echo

done

# Exit non-zero if any workflow failed or dispatch failed (useful for CI gating)
overall_ok=true
for WF in "${WF_ARRAY[@]}"; do
  WF_TRIMMED="$(echo "$WF" | xargs)"
  [[ -z "$WF_TRIMMED" ]] && continue
  rec="${RUN_RECORD_JSON[$WF_TRIMMED]:-}"
  [[ -z "$rec" ]] && continue
  s="$(echo "$rec" | jq -r '.status')"
  c="$(echo "$rec" | jq -r '.conclusion')"
  d="$(echo "$rec" | jq -r '.dispatch_status')"
  if [[ "$d" == "dispatch_failed" || "$c" == "failure" || "$c" == "timed_out" || "$s" != "completed" ]]; then
    overall_ok=false
  fi

done

if [[ "$overall_ok" == "true" ]]; then
  echo "All workflows resolved successfully."
else
  echo "One or more workflows did not resolve successfully."
  exit 2
fi
