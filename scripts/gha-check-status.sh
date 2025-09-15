#!/usr/bin/env bash
# gha-check-status.sh - Check status of dispatched workflows
# Companion script for gha-simple-dispatch.sh
# Requirements: gh >= 2.0, jq
set -euo pipefail

if ! command -v gh >/dev/null 2>&1; then
  echo "ERROR: gh CLI is required. https://cli.github.com/" >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: jq is required. https://stedolan.github.io/jq/" >&2
  exit 1
fi

# Environment variables
OWNER="${OWNER:-mhold3n}"
REPO="${REPO:-CamProV5}"
repo_slug="$OWNER/$REPO"

usage() {
  echo "Usage: $0 [timestamp] [workflow1,workflow2,...]"
  echo "       $0 --results-file <file.json>"
  echo
  echo "Arguments:"
  echo "  timestamp: RFC3339 timestamp (default: 5 minutes ago)"
  echo "  workflows: comma-separated list (default: from results file or common workflows)"
  echo
  echo "Options:"
  echo "  --results-file: JSON file from gha-simple-dispatch.sh (SAVE_RESULTS=true)"
  echo
  echo "Examples:"
  echo "  $0  # Check recent runs from last 5 minutes"
  echo "  $0 2025-09-15T06:40:00Z files-to-issues.yml,python.yml"
  echo "  $0 --results-file gha-dispatch-1694764800.json"
  echo
  echo "Environment variables:"
  echo "  OWNER: GitHub org/user (default: mhold3n)"
  echo "  REPO: GitHub repo (default: CamProV5)"
}

# Parse command line arguments
results_file=""
since_time=""
workflows=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --results-file)
      results_file="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
    *)
      if [[ -z "$since_time" ]]; then
        since_time="$1"
      elif [[ -z "$workflows" ]]; then
        workflows="$1"
      else
        echo "Too many arguments" >&2
        usage >&2
        exit 1
      fi
      shift
      ;;
  esac
done

# Load from results file if specified
if [[ -n "$results_file" ]]; then
  if [[ ! -f "$results_file" ]]; then
    echo "ERROR: Results file not found: $results_file" >&2
    exit 1
  fi
  
  echo "📄 Loading from results file: $results_file"
  since_time="$(jq -r '.timestamp' < "$results_file")"
  successful_workflows="$(jq -r '.successful[]?' < "$results_file" | tr '\n' ',')"
  failed_workflows="$(jq -r '.failed[]?' < "$results_file" | tr '\n' ',')"
  workflows="${successful_workflows}${failed_workflows}"
  workflows="${workflows%,}"  # Remove trailing comma
  
  echo "📅 Checking workflows dispatched at: $since_time"
  echo "🔍 Target workflows: $workflows"
  echo
fi

# Set defaults if not provided
if [[ -z "$since_time" ]]; then
  since_time="$(date -u -v-5M +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -d '5 minutes ago' +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || echo "2025-09-15T06:30:00Z")"
fi

if [[ -z "$workflows" ]]; then
  workflows="files-to-issues.yml,python.yml,issues-downsync.yml,release-drafter.yml,shared-indexes-smoke.yml"
fi

# Function to check recent runs for workflows
check_recent_runs() {
  local since_time="$1"
  local workflows="$2"
  
  echo "🔍 Checking workflows since: $since_time"
  echo
  
  IFS=',' read -r -a wf_array <<< "$workflows"
  local total_checked=0
  local found_runs=0
  local successful_runs=0
  local failed_runs=0
  local running_runs=0
  local queued_runs=0
  
  for wf in "${wf_array[@]}"; do
    wf_trimmed="$(echo "$wf" | xargs)"
    [[ -z "$wf_trimmed" ]] && continue
    
    total_checked=$((total_checked + 1))
    
    # Get recent runs for this workflow
    recent_runs="$(gh api "repos/$repo_slug/actions/workflows/$wf_trimmed/runs" \
      -q ".workflow_runs[] | select(.created_at >= \"$since_time\") | {status, conclusion, html_url, created_at, head_branch}" 2>/dev/null || echo "")"
    
    if [[ -n "$recent_runs" ]]; then
      found_runs=$((found_runs + 1))
      
      # Process each run (there might be multiple)
      while IFS= read -r run_info; do
        [[ -z "$run_info" ]] && continue
        
        status="$(echo "$run_info" | jq -r '.status')"
        conclusion="$(echo "$run_info" | jq -r '.conclusion // "pending"')"
        created="$(echo "$run_info" | jq -r '.created_at')"
        branch="$(echo "$run_info" | jq -r '.head_branch')"
        url="$(echo "$run_info" | jq -r '.html_url')"
        
        case "$status" in
          "completed") 
            if [[ "$conclusion" == "success" ]]; then
              echo "✅ $wf_trimmed - Completed successfully ($branch @ $created)"
              successful_runs=$((successful_runs + 1))
            elif [[ "$conclusion" == "skipped" ]]; then
              echo "⏭️  $wf_trimmed - Skipped ($branch @ $created)"
            else
              echo "❌ $wf_trimmed - Failed ($conclusion) - $url"
              failed_runs=$((failed_runs + 1))
            fi
            ;;
          "in_progress") 
            echo "🔄 $wf_trimmed - Running ($branch @ $created)"
            running_runs=$((running_runs + 1))
            ;;
          "queued") 
            echo "⏳ $wf_trimmed - Queued ($branch @ $created)"
            queued_runs=$((queued_runs + 1))
            ;;
          *) 
            echo "❓ $wf_trimmed - Unknown status ($status/$conclusion)"
            ;;
        esac
      done <<< "$(echo "$recent_runs" | jq -c '.')"
    else
      echo "⚪ $wf_trimmed - No recent runs found"
    fi
  done
  
  # Summary
  echo
  echo "📊 Summary:"
  echo "  🔍 Workflows checked: $total_checked"
  echo "  📋 Workflows with runs: $found_runs"
  echo "  ✅ Successful: $successful_runs"
  echo "  ❌ Failed: $failed_runs"
  echo "  🔄 Running: $running_runs"
  echo "  ⏳ Queued: $queued_runs"
  
  if [[ $failed_runs -gt 0 ]]; then
    echo
    echo "💡 To investigate failures:"
    echo "  gh run list --repo $repo_slug --status failure --created='>${since_time}'"
    echo "  gh run view --repo $repo_slug <run-id>"
  fi
}

# Main execution
echo "🔎 GitHub Actions Status Checker"
echo "Repository: $repo_slug"
echo

# Validate repository access
if ! gh api "repos/$repo_slug" -q '.name' >/dev/null 2>&1; then
  echo "ERROR: Cannot access repository $repo_slug" >&2
  echo "Check your GitHub authentication and repository permissions." >&2
  exit 1
fi

check_recent_runs "$since_time" "$workflows"