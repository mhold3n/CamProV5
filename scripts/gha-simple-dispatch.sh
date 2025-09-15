#!/usr/bin/env bash
# gha-simple-dispatch.sh - Event-driven workflow testing
# Simple, reliable GitHub Actions workflow dispatcher that eliminates API polling issues
# Requirements: gh >= 2.0
set -euo pipefail

if ! command -v gh >/dev/null 2>&1; then
  echo "ERROR: gh CLI is required. https://cli.github.com/" >&2
  exit 1
fi

# Environment variables with backward compatibility
OWNER="${OWNER:-mhold3n}"
REPO="${REPO:-CamProV5}" 
REF="${REF:-main}"
repo_slug="$OWNER/$REPO"

# Extract workflows from current system or use sensible defaults (only workflows with workflow_dispatch)
DEFAULT_WORKFLOWS="files-to-issues.yml,python.yml,issues-downsync.yml,release-drafter.yml,shared-indexes-smoke.yml"
WORKFLOWS="${WORKFLOWS:-$DEFAULT_WORKFLOWS}"

# New event-driven specific options
SHOW_URLS="${SHOW_URLS:-true}"
SAVE_RESULTS="${SAVE_RESULTS:-false}"
RESULTS_FILE="${RESULTS_FILE:-gha-dispatch-$(date +%s).json}"
VERBOSE="${VERBOSE:-false}"
DEBUG="${DEBUG:-false}"

# Helper functions for backward compatibility
log_verbose() {
  [[ "$VERBOSE" == "true" ]] && echo "   [VERBOSE] $*" >&2
}

log_debug() {
  [[ "$DEBUG" == "true" ]] && echo "   [DEBUG] $*" >&2
}

# Check if workflow supports manual dispatch by examining YAML content
supports_dispatch() {
  local wf="$1"
  local yaml_content
  
  log_debug "Checking workflow_dispatch support for $wf"
  
  # Add timeout and better error handling for API calls
  if yaml_content="$(gh api -H "Accept: application/vnd.github.raw" \
    "repos/$repo_slug/contents/.github/workflows/$wf?ref=$REF" 2>/dev/null)"; then
    log_debug "Successfully fetched YAML content for $wf"
    if echo "$yaml_content" | grep -qE '(^|[[:space:]])workflow_dispatch:'; then
      log_debug "Found workflow_dispatch trigger in $wf"
      return 0
    else
      log_debug "No workflow_dispatch trigger found in $wf"
      return 1
    fi
  else
    log_debug "Failed to fetch YAML content for $wf (workflow may not exist)"
    return 1
  fi
}

# Generate comprehensive summary and next steps
generate_summary() {
  local timestamp="$1"
  
  echo
  echo "📋 Dispatch Summary ($(date -u +"%H:%M:%S")):"
  echo "  ✅ Successful: ${#dispatch_results[@]}"
  echo "  ❌ Failed: ${#failed_workflows[@]}"
  echo
  
  if [[ ${#dispatch_results[@]} -gt 0 ]]; then
    echo "🔍 Monitor workflow progress:"
    if [[ "$SHOW_URLS" == "true" ]]; then
      echo "  GitHub UI: https://github.com/$repo_slug/actions"
      echo "  CLI: gh run list --repo $repo_slug --created='>${timestamp}'"
      echo "  CLI (watch): gh run watch --repo $repo_slug"
    fi
    echo
    echo "💡 Check specific workflow status:"
    for wf in "${dispatch_results[@]}"; do
      echo "  gh run list --workflow='$wf' --repo $repo_slug"
    done
    echo
  fi
  
  if [[ ${#failed_workflows[@]} -gt 0 ]]; then
    echo "❌ Failed workflows:"
    for wf in "${failed_workflows[@]}"; do
      echo "  $wf"
    done
    echo
  fi
  
  # Optional results persistence
  if [[ "$SAVE_RESULTS" == "true" ]]; then
    {
      echo "{"
      echo "  \"timestamp\": \"$timestamp\","
      echo "  \"repository\": \"$repo_slug\","
      echo "  \"ref\": \"$REF\","
      echo "  \"successful\": ["
      if [[ ${#dispatch_results[@]} -gt 0 ]]; then
        printf '    "%s"' "${dispatch_results[0]}"
        for ((i=1; i<${#dispatch_results[@]}; i++)); do
          printf ',\n    "%s"' "${dispatch_results[i]}"
        done
        echo
      fi
      echo "  ],"
      echo "  \"failed\": ["
      if [[ ${#failed_workflows[@]} -gt 0 ]]; then
        printf '    "%s"' "${failed_workflows[0]}"
        for ((i=1; i<${#failed_workflows[@]}; i++)); do
          printf ',\n    "%s"' "${failed_workflows[i]}"
        done
        echo
      fi
      echo "  ]"
      echo "}"
    } > "$RESULTS_FILE"
    echo "📄 Results saved to: $RESULTS_FILE"
  fi
  
  # Exit with error code if any workflows failed to dispatch
  [[ ${#failed_workflows[@]} -eq 0 ]]
}

# Validate required parameters
if [[ -z "$OWNER" || -z "$REPO" || -z "$REF" ]]; then
  echo "Usage: OWNER=... REPO=... REF=... [WORKFLOWS='file.yml,file2.yml'] $0" >&2
  exit 1
fi

# Main execution begins
echo "🚀 Dispatching workflows on $repo_slug at ref '$REF'..."
if [[ "$WORKFLOWS" == "$DEFAULT_WORKFLOWS" ]]; then
  echo "Using default workflows (only those with workflow_dispatch support)"
fi
echo

# Track results for summary
dispatch_results=()
failed_workflows=()
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Parse workflows and process each one
IFS=',' read -r -a workflows <<< "$WORKFLOWS"

for wf in "${workflows[@]}"; do
  wf_trimmed="$(echo "$wf" | xargs)"
  [[ -z "$wf_trimmed" ]] && continue
  
  log_debug "Processing workflow: $wf_trimmed"
  
  # Check if workflow supports manual dispatch
  if ! supports_dispatch "$wf_trimmed"; then
    echo "⏭️  $wf_trimmed - No workflow_dispatch trigger (skipped)"
    log_verbose "Workflow $wf_trimmed does not support manual dispatch"
    continue
  fi
  
  log_debug "Workflow $wf_trimmed supports dispatch, attempting..."
  
  # Attempt dispatch with error capture
  if gh api -X POST "repos/$repo_slug/actions/workflows/$wf_trimmed/dispatches" \
     -H "Accept: application/vnd.github+json" \
     -f "ref=$REF" >/dev/null 2>&1; then
    echo "✅ $wf_trimmed - Dispatched successfully"
    dispatch_results+=("$wf_trimmed")
    log_debug "Successfully dispatched $wf_trimmed"
  else
    echo "❌ $wf_trimmed - Dispatch failed"
    failed_workflows+=("$wf_trimmed")
    log_debug "Failed to dispatch $wf_trimmed"
  fi
done

# Generate results summary and next steps
generate_summary "$timestamp"