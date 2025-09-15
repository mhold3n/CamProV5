#!/usr/bin/env bash
# monitor-critical-workflows.sh - Phase 4: Workflow monitoring dashboard
# Monitors critical workflows and provides health status
set -euo pipefail

OWNER="${OWNER:-mhold3n}"
REPO="${REPO:-CamProV5}"
repo_slug="$OWNER/$REPO"
CRITICAL_WORKFLOWS="files-to-issues.yml,python.yml,issues-downsync.yml,shared-indexes-smoke.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

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

log_header() {
    echo -e "${BOLD}$*${NC}"
}

main() {
    echo "🔍 Monitoring critical workflows..."
    ./scripts/gha-check-status.sh "$(date -u -v-30M +"%Y-%m-%dT%H:%M:%SZ")" "$CRITICAL_WORKFLOWS"
}

main "$@"