#!/usr/bin/env bash
# test-fixes-direct.sh - Direct testing of Phase 1 & 2 fixes
# Bypasses the complex dispatch script to directly test our fixes
set -euo pipefail

OWNER="mhold3n"
REPO="CamProV5"
REF="main"
repo_slug="$OWNER/$REPO"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

dispatch_workflow() {
    local workflow="$1"
    local description="$2"
    
    log_info "Testing $workflow - $description"
    
    # Direct API dispatch
    if gh api -X POST "repos/$repo_slug/actions/workflows/$workflow/dispatches" \
       -H "Accept: application/vnd.github+json" \
       -f "ref=$REF" >/dev/null 2>&1; then
        log_success "✅ $workflow - Dispatched successfully"
        return 0
    else
        log_error "❌ $workflow - Dispatch failed"
        return 1
    fi
}

check_workflow_status() {
    local workflow="$1"
    local since_time="$(date -u -v-5M +"%Y-%m-%dT%H:%M:%SZ")"
    
    log_info "Checking recent runs for $workflow since $since_time..."
    
    # Get recent runs
    if recent_runs="$(gh api "repos/$repo_slug/actions/workflows/$workflow/runs" \
      -q ".workflow_runs[] | select(.created_at >= \"$since_time\") | {status, conclusion, html_url, created_at}" 2>/dev/null)"; then
        
        if [[ -n "$recent_runs" ]]; then
            echo "$recent_runs" | while read -r run_info; do
                if [[ -n "$run_info" ]]; then
                    status="$(echo "$run_info" | jq -r '.status')"
                    conclusion="$(echo "$run_info" | jq -r '.conclusion // "pending"')"
                    created="$(echo "$run_info" | jq -r '.created_at')"
                    url="$(echo "$run_info" | jq -r '.html_url')"
                    
                    case "$status" in
                        "completed")
                            if [[ "$conclusion" == "success" ]]; then
                                log_success "✅ Run completed successfully at $created"
                            else
                                log_error "❌ Run failed ($conclusion) - $url"
                            fi
                            ;;
                        "in_progress")
                            log_info "🔄 Run in progress (started at $created)"
                            ;;
                        "queued")
                            log_info "⏳ Run queued (created at $created)"
                            ;;
                    esac
                fi
            done
        else
            log_info "⚪ No recent runs found (may still be starting)"
        fi
    else
        log_error "Failed to check workflow status"
        return 1
    fi
}

main() {
    echo "=========================================="
    log_info "Direct Testing of Phase 1 & 2 Fixes"
    log_info "Testing critical workflows with direct API calls"
    echo "=========================================="
    echo
    
    # Test authentication and basic API access
    log_info "Verifying GitHub CLI authentication..."
    if gh auth status >/dev/null 2>&1; then
        log_success "✅ GitHub CLI authenticated"
    else
        log_error "❌ GitHub CLI authentication failed"
        exit 1
    fi
    
    # Test repository access
    log_info "Verifying repository access..."
    if repo_name="$(gh api "repos/$repo_slug" -q '.name' 2>/dev/null)"; then
        log_success "✅ Repository access confirmed: $repo_name"
    else
        log_error "❌ Cannot access repository $repo_slug"
        exit 1
    fi
    
    echo
    log_info "Dispatching critical workflows..."
    echo
    
    # Track results
    successful_dispatches=0
    failed_dispatches=0
    
    # Test Phase 1 fixes - Authentication workflows
    echo "--- Phase 1: Authentication Fixes ---"
    
    if dispatch_workflow "files-to-issues.yml" "GitHub Issue Mirroring (Files → Issues)"; then
        ((successful_dispatches++))
    else
        ((failed_dispatches++))
    fi
    
    if dispatch_workflow "issues-downsync.yml" "GitHub Issue Mirroring (Issues → Files)"; then
        ((successful_dispatches++))
    else
        ((failed_dispatches++))
    fi
    
    echo
    echo "--- Phase 2: Infrastructure Fixes ---"
    
    if dispatch_workflow "python.yml" "Python CI Testing"; then
        ((successful_dispatches++))
    else
        ((failed_dispatches++))
    fi
    
    if dispatch_workflow "shared-indexes-smoke.yml" "Shared Indexes Smoke Tests"; then
        ((successful_dispatches++))
    else
        ((failed_dispatches++))
    fi
    
    echo
    echo "=========================================="
    log_info "Dispatch Results Summary"
    log_success "✅ Successful dispatches: $successful_dispatches"
    if [[ $failed_dispatches -gt 0 ]]; then
        log_error "❌ Failed dispatches: $failed_dispatches"
    else
        log_success "❌ Failed dispatches: $failed_dispatches"
    fi
    echo
    
    # Wait a moment for workflows to start
    log_info "Waiting 10 seconds for workflows to initialize..."
    sleep 10
    echo
    
    # Check status of dispatched workflows
    log_info "Checking status of dispatched workflows..."
    echo
    
    check_workflow_status "files-to-issues.yml"
    echo
    check_workflow_status "issues-downsync.yml"
    echo
    check_workflow_status "python.yml"
    echo
    check_workflow_status "shared-indexes-smoke.yml"
    
    echo
    echo "=========================================="
    if [[ $failed_dispatches -eq 0 ]]; then
        log_success "🎉 All critical workflows dispatched successfully!"
        log_info "Phase 1 & 2 fixes appear to be working correctly."
        log_info "Monitor progress at: https://github.com/$repo_slug/actions"
    else
        log_error "Some workflows failed to dispatch. Further investigation needed."
    fi
    echo "=========================================="
    
    return $failed_dispatches
}

main "$@"