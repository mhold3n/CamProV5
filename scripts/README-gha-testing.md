# GitHub Actions Testing - Event-Driven Approach

This directory contains the new event-driven GitHub Actions workflow testing system that replaces the complex polling-based approach.

## 🚀 Quick Start

### Dispatch workflows and get immediate feedback
```bash
# Dispatch default workflows (those with workflow_dispatch support)
./scripts/gha-simple-dispatch.sh

# Dispatch specific workflows
WORKFLOWS="files-to-issues.yml,python.yml" ./scripts/gha-simple-dispatch.sh

# With verbose output
VERBOSE=true ./scripts/gha-simple-dispatch.sh
```

### Check workflow status after dispatch
```bash
# Check recent runs from last 5 minutes
./scripts/gha-check-status.sh

# Check specific workflows since a timestamp
./scripts/gha-check-status.sh 2025-09-15T06:40:00Z files-to-issues.yml,python.yml

# Monitor in GitHub UI or CLI
gh run list --repo $OWNER/$REPO
gh run watch --repo $OWNER/$REPO
```

## 📋 Scripts Overview

### `gha-simple-dispatch.sh` - Main Dispatcher

Simple, reliable workflow dispatcher that eliminates API polling issues.

**Features:**
- ✅ Instant dispatch feedback
- ✅ No API reliability issues
- ✅ Simpler debugging
- ✅ Clear next steps provided
- ✅ Environment variable compatibility

**Environment Variables:**
- `OWNER` - GitHub org/user (default: mhold3n)
- `REPO` - GitHub repo (default: CamProV5)
- `REF` - Git ref to dispatch (default: main)
- `WORKFLOWS` - Comma-separated workflow files (default: dispatch-enabled workflows)
- `VERBOSE` - Enable verbose output (default: false)
- `DEBUG` - Enable debug output (default: false)
- `SAVE_RESULTS` - Save results to JSON file (default: false)
- `SHOW_URLS` - Show GitHub UI and CLI URLs (default: true)

**Examples:**
```bash
# Basic usage
./scripts/gha-simple-dispatch.sh

# Custom repository and workflows
OWNER=myorg REPO=myrepo WORKFLOWS="ci.yml,test.yml" ./scripts/gha-simple-dispatch.sh

# Save results for later status checking
SAVE_RESULTS=true ./scripts/gha-simple-dispatch.sh

# Debug mode
DEBUG=true ./scripts/gha-simple-dispatch.sh
```

### `gha-check-status.sh` - Status Checker

Optional companion script for programmatic status checking.

**Features:**
- 🔍 Check workflow run status since timestamp
- 📄 Load from dispatch results file
- 📊 Statistical summaries
- 💡 Helpful investigation commands
- 🎯 Multiple output formats

**Examples:**
```bash
# Check recent runs
./scripts/gha-check-status.sh

# Check specific time and workflows
./scripts/gha-check-status.sh 2025-09-15T06:40:00Z python.yml,ci.yml

# Load from saved dispatch results
SAVE_RESULTS=true ./scripts/gha-simple-dispatch.sh
./scripts/gha-check-status.sh --results-file gha-dispatch-*.json
```

## 🔄 Migration from Old System

### Old Way (Complex Polling - Deprecated)
```bash
# 5+ minutes execution time, complex debugging, API reliability issues
./scripts/gha-repeatable-workflow-test.sh
```

### New Way (Simple Dispatch - Recommended)
```bash
# 10 seconds execution time, clear output, no API issues
./scripts/gha-simple-dispatch.sh
```

## 📈 Benefits of New Approach

| Aspect | Old System | New System |
|--------|------------|------------|
| **Execution Time** | 5+ minutes | 10 seconds |
| **API Calls per Test** | 100+ | 6-10 |
| **Failure Modes** | Multiple complex scenarios | Simple dispatch success/fail |
| **Maintenance** | 876 lines of complex code | 169 lines of simple code |
| **Debug Complexity** | Extensive logs and timing issues | Clear success/failure output |
| **API Reliability** | Frequent polling failures | No polling, no reliability issues |

## 💡 Usage Patterns

### For Development Testing
```bash
# Quick test of critical workflows
WORKFLOWS="files-to-issues.yml,python.yml" ./scripts/gha-simple-dispatch.sh

# Monitor progress in GitHub UI
# (URLs provided in script output)
```

### For CI Integration
```bash
# Dispatch and save results
SAVE_RESULTS=true ./scripts/gha-simple-dispatch.sh

# Later check results programmatically
./scripts/gha-check-status.sh --results-file gha-dispatch-*.json
```

### For Debugging
```bash
# Detailed execution logging
DEBUG=true VERBOSE=true ./scripts/gha-simple-dispatch.sh

# Check what went wrong
./scripts/gha-check-status.sh 2025-09-15T06:00:00Z
```

## 🔍 Monitoring Workflow Progress

After dispatching workflows, you have several options to monitor progress:

### GitHub UI (Recommended)
- Visit the provided GitHub Actions URL
- Real-time status updates
- Full logs and job details

### GitHub CLI
```bash
# List recent runs
gh run list --repo $OWNER/$REPO --created='>2025-09-15T06:40:00Z'

# Watch runs in real-time
gh run watch --repo $OWNER/$REPO

# View specific run details
gh run view --repo $OWNER/$REPO <run-id>

# Check specific workflow
gh run list --workflow='python.yml' --repo $OWNER/$REPO
```

### Status Checker Script
```bash
# Check status periodically
./scripts/gha-check-status.sh

# Get detailed summary
./scripts/gha-check-status.sh 2025-09-15T06:40:00Z python.yml,files-to-issues.yml
```

## 🏗 Architecture

The new system eliminates complexity through:

1. **Event-Driven Design**: Dispatch and report immediately, no waiting
2. **Separation of Concerns**: Dispatch ≠ Status Checking
3. **GitHub-Native Tools**: Leverage GitHub UI and CLI for monitoring
4. **Fail-Fast**: Clear error reporting, no complex retry logic
5. **Backward Compatibility**: Same environment variables and exit codes

## 🚨 Troubleshooting

### Workflow Dispatch Failed
```bash
# Check if workflow supports manual dispatch
DEBUG=true ./scripts/gha-simple-dispatch.sh

# Common issues:
# - Workflow file doesn't have 'workflow_dispatch:' trigger
# - Workflow file doesn't exist at the specified ref
# - Authentication or permission issues
```

### No Recent Runs Found
```bash
# Verify dispatch was successful (check script output)
# Workflows may take a few seconds to appear in GitHub's API
# Check GitHub UI directly for most up-to-date status
```

### Authentication Issues
```bash
# Verify GitHub CLI authentication
gh auth status

# Re-authenticate if needed
gh auth login
```

## 📚 References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub CLI Documentation](https://cli.github.com/manual/)
- [workflow_dispatch Event](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#workflow_dispatch)

---

> **Note**: The old `gha-repeatable-workflow-test.sh` script has been archived but is still available for reference. The new event-driven approach is recommended for all new usage.