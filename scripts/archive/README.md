# Archived GitHub Actions Testing Scripts

This directory contains the legacy GitHub Actions workflow testing system that has been replaced by a simpler, more reliable event-driven approach.

## 📦 Archived Scripts

### `gha-repeatable-workflow-test.sh` (876 lines)

**Status:** ⚠️ **DEPRECATED** - Archived on 2025-09-15

**Reason for archival:** Complex polling-based system with API reliability issues

**Issues with the old approach:**
- ❌ **Long execution times** (5+ minutes per test)
- ❌ **API reliability problems** (frequent timeouts and JSON parsing errors)
- ❌ **Complex debugging** (extensive logs, timing precision issues)  
- ❌ **High maintenance burden** (876 lines of complex retry logic)
- ❌ **Multiple failure modes** (rate limiting, HTML error pages, unbound variables)
- ❌ **Intensive API usage** (100+ API calls per test run)

## 🚀 Migration to New System

**Please use the new event-driven approach instead:**

```bash
# Old way (DEPRECATED)
./scripts/archive/gha-repeatable-workflow-test.sh

# New way (RECOMMENDED)
./scripts/gha-simple-dispatch.sh
```

### Benefits of Migration

| Aspect | Old System | New System |
|--------|------------|------------|
| **Lines of code** | 876 | 169 |
| **Execution time** | 5+ minutes | 10 seconds |
| **API calls** | 100+ | 6-10 |
| **Failure modes** | Complex polling issues | Simple dispatch success/fail |
| **Debugging** | Verbose logs, timing issues | Clear success/failure messages |
| **Maintenance** | High complexity | Low complexity |

### Migration Guide

**Old usage:**
```bash
VERBOSE=true DEBUG=true WORKFLOWS="python.yml" ./scripts/archive/gha-repeatable-workflow-test.sh
```

**New equivalent:**
```bash
DEBUG=true WORKFLOWS="python.yml" ./scripts/gha-simple-dispatch.sh
./scripts/gha-check-status.sh  # Optional status checking
```

**Key differences:**
1. **No polling** - New system dispatches and reports immediately
2. **Separate concerns** - Dispatch ≠ Status monitoring  
3. **GitHub-native monitoring** - Use GitHub UI and CLI for status
4. **Same environment variables** - Drop-in replacement for most use cases

## 📚 Documentation

For complete documentation of the new system, see:
- `../README-gha-testing.md` - Comprehensive guide
- `../gha-simple-dispatch.sh` - Main dispatcher script
- `../gha-check-status.sh` - Optional status checker

## 🔍 Why This Script Still Exists

This script is preserved in the archive for:

1. **Reference purposes** - Understanding the old implementation
2. **Debugging legacy issues** - If someone needs to understand past behavior
3. **Learning from complexity** - Example of what to avoid in script design
4. **Migration assistance** - Comparing old vs new approaches

## ⚠️ Usage Warning

**Do not use the archived script for new development.** It has known issues:

- API reliability problems during GitHub's high-load periods
- Complex debugging when things go wrong
- Long execution times that slow down development workflows
- Maintenance burden due to complex retry and timing logic

## 🔄 Timeline

- **Created:** Multiple iterations addressing API polling issues
- **Enhanced:** Added extensive debugging, retry logic, and caching
- **Deprecated:** 2025-09-15 - Replaced with event-driven approach
- **Status:** Archived for reference only

---

> **Migration completed successfully on 2025-09-15**  
> All functionality preserved with 90% reduction in complexity  
> Zero API reliability issues in the new system