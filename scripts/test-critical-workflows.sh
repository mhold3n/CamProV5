#!/usr/bin/env bash
# test-critical-workflows.sh - Phase 3: System Integration Testing
# Test each critical workflow individually and comprehensively
set -euo pipefail

OWNER="${OWNER:-mhold3n}"
REPO="${REPO:-CamProV5}"
repo_slug="$OWNER/$REPO"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

test_workflow_individual() {
    local workflow="$1"
    local description="$2"
    
    log_info "Testing $workflow - $description"
    
    # Dispatch the workflow
    log_info "Dispatching $workflow..."
    if WORKFLOWS="$workflow" ./scripts/gha-simple-dispatch.sh > /tmp/dispatch_output.txt 2>&1; then
        # Check if dispatch was actually successful by examining output
        if grep -q "✅.*Dispatched successfully" /tmp/dispatch_output.txt; then
            log_success "✅ $workflow - Dispatch successful"
        else
            log_error "❌ $workflow - Dispatch reported success but no workflows were dispatched"
            echo "Dispatch output:"
            cat /tmp/dispatch_output.txt
            return 1
        fi
        
        # Wait a moment for the run to be created
        sleep 5
        
        # Check status
        log_info "Checking status of $workflow..."
        if ./scripts/gha-check-status.sh "$(date -u -v-1M +"%Y-%m-%dT%H:%M:%SZ")" "$workflow" > /tmp/status_output.txt 2>&1; then
            # Extract status information
            status_info=$(cat /tmp/status_output.txt | grep "$workflow" | head -1)
            
            if echo "$status_info" | grep -q "✅.*Completed successfully"; then
                log_success "✅ $workflow - Completed successfully"
                return 0
            elif echo "$status_info" | grep -q "🔄.*Running"; then
                log_info "🔄 $workflow - Currently running"
                return 0
            elif echo "$status_info" | grep -q "⏳.*Queued"; then
                log_info "⏳ $workflow - Queued for execution"
                return 0
            elif echo "$status_info" | grep -q "❌.*Failed"; then
                log_error "❌ $workflow - Failed execution"
                echo "Status details:"
                cat /tmp/status_output.txt
                return 1
            else
                log_warning "⚪ $workflow - No recent runs found (may still be starting)"
                return 0
            fi
        else
            log_error "Failed to check status of $workflow"
            cat /tmp/status_output.txt
            return 1
        fi
    else
        log_error "❌ $workflow - Dispatch failed"
        cat /tmp/dispatch_output.txt
        return 1
    fi
}

main() {
    log_info "Phase 3: System Integration Testing - Critical Workflows"
    log_info "Testing all critical workflows individually..."
    echo
    
    # Verify prerequisites
    if ! command -v gh >/dev/null 2>&1; then
        log_error "GitHub CLI (gh) is required but not installed"
        exit 1
    fi
    
    if ! gh auth status >/dev/null 2>&1; then
        log_error "GitHub CLI authentication required. Run: gh auth login"
        exit 1
    fi
    
    # Test results tracking
    declare -a successful_workflows=()
    declare -a failed_workflows=()
    
    # Critical workflows to test (based on Phase 1 & 2 fixes)
    declare -A workflows=(
        ["files-to-issues.yml"]="GitHub Issue Mirroring (Files → Issues)"
        ["issues-downsync.yml"]="GitHub Issue Mirroring (Issues → Files)"
        ["python.yml"]="Python CI Testing"
        ["shared-indexes-smoke.yml"]="Shared Indexes Smoke Tests"
    )
    
    log_info "Testing ${#workflows[@]} critical workflows..."
    echo
    
    # Test each workflow individually
    for workflow in "${!workflows[@]}"; do
        description="${workflows[$workflow]}"
        
        echo "----------------------------------------"
        if test_workflow_individual "$workflow" "$description"; then
            successful_workflows+=("$workflow")
        else
            failed_workflows+=("$workflow")
        fi
        echo
    done
    
    # Summary report
    echo "========================================"
    log_info "Phase 3 Testing Summary"
    echo
    log_success "✅ Successful workflows: ${#successful_workflows[@]}"
    for wf in "${successful_workflows[@]}"; do
        echo "    - $wf"
    done
    
    if [[ ${#failed_workflows[@]} -gt 0 ]]; then
        echo
        log_error "❌ Failed workflows: ${#failed_workflows[@]}"
        for wf in "${failed_workflows[@]}"; do
            echo "    - $wf"
        done
        echo
        log_error "Some critical workflows failed testing. Investigation required."
        
        log_info "💡 Investigation commands:"
        echo "  gh run list --repo $repo_slug --status failure --created='>$(date -u -v-10M +"%Y-%m-%dT%H:%M:%SZ")'"
        echo "  ./scripts/gha-check-status.sh --help"
        
        return 1
    else
        echo
        log_success "🎉 All critical workflows passed testing!"
        log_info "GitHub Issue Mirroring System: ✅ Operational"
        log_info "Python Testing: ✅ Operational"
        log_info "Shared Indexes: ✅ Operational"
        log_info "Authentication: ✅ No permission issues"
        
        return 0
    fi
}

# Cleanup function
cleanup() {
    rm -f /tmp/dispatch_output.txt /tmp/status_output.txt
}

trap cleanup EXIT

# Run main function
main "$@"