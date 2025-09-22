(base) maxholden@MacBookPro CamProV5 % VERBOSE=true DEBUG=true ./scripts/gha-repeatable-workflow-test.sh
WORKFLOWS not provided; using default workflows list:
ci.yml,codeql.yml,dependency-review.yml,files-to-issues.yml,files_to_issues.yml,guard-shared-indexes.yml,issues-downsync.yml,labeler.yml,pr-title-lint.yml,python-ci.yml,python.yml,release-drafter.yml,release.yml,shared-indexes-smoke.yml,todos_to_issues.yml
Dispatching workflows on mhold3n/CamProV5 at ref 'main'...
- Dispatching: ci.yml with inputs: {}
  -> Pre-check: workflow_dispatch NOT present (skipping dispatch)
- Dispatching: codeql.yml with inputs: {}
  -> Pre-check: workflow_dispatch NOT present (skipping dispatch)
- Dispatching: dependency-review.yml with inputs: {}
  -> Pre-check: workflow_dispatch NOT present (skipping dispatch)
- Dispatching: files-to-issues.yml with inputs: {}
  -> Pre-check: workflow_dispatch present
  -> Workflow diagnostics:
  ID: 187641376
  State: active
  List handle: 187641376
  Previous runs: 18
  Target ref 'main': main
  [DEBUG] Confirmed recent run creation for files-to-issues.yml
- Dispatching: files_to_issues.yml with inputs: {}
  -> Pre-check: workflow_dispatch present
  -> Workflow diagnostics:
  ID: 186334116
  State: active
  List handle: 186334116
  Previous runs: 11
  Target ref 'main': main
  [DEBUG] Confirmed recent run creation for files_to_issues.yml
- Dispatching: guard-shared-indexes.yml with inputs: {}
  -> Pre-check: workflow_dispatch NOT present (skipping dispatch)
- Dispatching: issues-downsync.yml with inputs: {}
  -> Pre-check: workflow_dispatch present
  -> Workflow diagnostics:
  ID: 187641377
  State: active
  List handle: 187641377
  Previous runs: 268
  Target ref 'main': main
  [DEBUG] Confirmed recent run creation for issues-downsync.yml
- Dispatching: labeler.yml with inputs: {}
  -> Pre-check: workflow_dispatch NOT present (skipping dispatch)
- Dispatching: pr-title-lint.yml with inputs: {}
  -> Pre-check: workflow_dispatch NOT present (skipping dispatch)
- Dispatching: python-ci.yml with inputs: {}
  -> Pre-check: workflow_dispatch NOT present (skipping dispatch)
- Dispatching: python.yml with inputs: {}
  -> Pre-check: workflow_dispatch present
  -> Workflow diagnostics:
  ID: 185372765
  State: active
  List handle: 185372765
  Previous runs: 16
  Target ref 'main': main
  [DEBUG] Confirmed recent run creation for python.yml
- Dispatching: release-drafter.yml with inputs: {}
  -> Pre-check: workflow_dispatch present
  -> Workflow diagnostics:
  ID: 185372766
  State: active
  List handle: 185372766
  Previous runs: 20
  Target ref 'main': main
- Dispatching: release.yml with inputs: {}
  -> Pre-check: workflow_dispatch NOT present (skipping dispatch)
- Dispatching: shared-indexes-smoke.yml with inputs: {}
  -> Pre-check: workflow_dispatch present
  -> Workflow diagnostics:
  ID: 187565896
  State: active
  List handle: 187565896
  Previous runs: 5
  Target ref 'main': main
- Dispatching: todos_to_issues.yml with inputs: {}
  -> Pre-check: workflow_dispatch NOT present (skipping dispatch)

=== DEBUG: Repository and workflow diagnostics ===
Repository permissions:
{
"permissions": {
"admin": true,
"maintain": true,
"pull": true,
"push": true,
"triage": true
},
"private": false
}
All workflows in repository:
CI: active (ID: 185372761)
CodeQL: active (ID: 185372762)
Dependency Review: active (ID: 187641375)
Mirror Repo Files → GitHub Issues: active (ID: 187641376)
Mirror Repo Files → GitHub Issues: active (ID: 186334116)
Guard Shared Indexes: active (ID: 187565990)
Mirror GitHub Issues → Repo Files: active (ID: 187641377)
PR Labeler: active (ID: 185372763)
PR Title Lint: active (ID: 185372764)
Python CI: active (ID: 187641378)
Python CI: active (ID: 185372765)
Release Drafter: active (ID: 185372766)
Release Build & Artifacts: active (ID: 185372767)
Shared Indexes Smoke: active (ID: 187565896)
TODOs → GitHub Issues: active (ID: 186334118)
Dependabot Updates: active (ID: 185372772)
Recent workflow runs:
Failed to cache repository runs data

[DEBUG] Caching repository runs data for polling fallback...
[DEBUG] Failed to cache repository runs data - live API calls may be unreliable
Polling workflow runs (timeout=300s, interval=5s)...
[DEBUG] Attempting to find run_id for files-to-issues.yml...
[DEBUG] Live API failed and no cached repository data available for files-to-issues.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:20:07.559906 -0700 PDT m=+0.072007076
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for files-to-issues.yml (handle: 187641376)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:17:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 1/12 failed for files-to-issues.yml (cushion: 0s)
[DEBUG] Live API failed and no cached repository data available for files-to-issues.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:20:10.119613 -0700 PDT m=+0.063914940
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for files-to-issues.yml (handle: 187641376)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:17:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 2/12 failed for files-to-issues.yml (cushion: 30s)
[DEBUG] Live API failed and no cached repository data available for files-to-issues.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:20:13.859926 -0700 PDT m=+0.073482586
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for files-to-issues.yml (handle: 187641376)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:16:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 3/12 failed for files-to-issues.yml (cushion: 60s)
[DEBUG] Live API failed and no cached repository data available for files-to-issues.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:20:19.63097 -0700 PDT m=+0.062291181
* Request to https://api.github.com/...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for files-to-issues.yml (handle: 187641376)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:16:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 4/12 failed for files-to-issues.yml (cushion: 90s)
[DEBUG] Live API failed and no cached repository data available for files-to-issues.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:20:29.278849 -0700 PDT m=+0.062974545
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for files-to-issues.yml (handle: 187641376)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:15:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 5/12 failed for files-to-issues.yml (cushion: 120s)
[DEBUG] Live API failed and no cached repository data available for files-to-issues.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:20:35.784417 -0700 PDT m=+0.062266939
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for files-to-issues.yml (handle: 187641376)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:15:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 6/12 failed for files-to-issues.yml (cushion: 150s)
[DEBUG] Live API failed and no cached repository data available for files-to-issues.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:20:42.331358 -0700 PDT m=+0.062034343
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for files-to-issues.yml (handle: 187641376)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:14:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 7/12 failed for files-to-issues.yml (cushion: 180s)
[DEBUG] Live API failed and no cached repository data available for files-to-issues.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:20:48.931355 -0700 PDT m=+0.063889889
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for files-to-issues.yml (handle: 187641376)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:14:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 8/12 failed for files-to-issues.yml (cushion: 210s)
[DEBUG] Live API failed and no cached repository data available for files-to-issues.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:20:55.508918 -0700 PDT m=+0.067041589
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for files-to-issues.yml (handle: 187641376)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:13:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 9/12 failed for files-to-issues.yml (cushion: 240s)
[DEBUG] Live API failed and no cached repository data available for files-to-issues.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:21:01.98068 -0700 PDT m=+0.062379241
* Request to https://api.github.com/...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for files-to-issues.yml (handle: 187641376)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:13:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 10/12 failed for files-to-issues.yml (cushion: 270s)
[DEBUG] Live API failed and no cached repository data available for files-to-issues.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:21:12.866572 -0700 PDT m=+0.064088058
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for files-to-issues.yml (handle: 187641376)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:12:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 11/12 failed for files-to-issues.yml (cushion: 300s)
[DEBUG] Live API failed and no cached repository data available for files-to-issues.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:21:19.3796 -0700 PDT m=+0.061914783
* Request to https://api.github.com/r...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for files-to-issues.yml (handle: 187641376)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:12:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 12/12 failed for files-to-issues.yml (cushion: 330s)
[DEBUG] No run_id found for files-to-issues.yml, remaining pending
[DEBUG] Attempting to find run_id for files_to_issues.yml...
[DEBUG] Live API failed and no cached repository data available for files_to_issues.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:21:25.980326 -0700 PDT m=+0.063015219
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for files_to_issues.yml (handle: 186334116)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:17:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 1/12 failed for files_to_issues.yml (cushion: 0s)
[DEBUG] Live API failed and no cached repository data available for files_to_issues.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:21:28.508281 -0700 PDT m=+0.066741676
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for files_to_issues.yml (handle: 186334116)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:17:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 2/12 failed for files_to_issues.yml (cushion: 30s)
[DEBUG] Live API failed and no cached repository data available for files_to_issues.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:21:32.058939 -0700 PDT m=+0.073924945
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for files_to_issues.yml (handle: 186334116)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:16:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 3/12 failed for files_to_issues.yml (cushion: 60s)
[DEBUG] Live API failed and no cached repository data available for files_to_issues.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:21:37.624788 -0700 PDT m=+0.062960616
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for files_to_issues.yml (handle: 186334116)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:16:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 4/12 failed for files_to_issues.yml (cushion: 90s)
[DEBUG] Live API failed and no cached repository data available for files_to_issues.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:21:47.208808 -0700 PDT m=+0.080950669
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for files_to_issues.yml (handle: 186334116)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:15:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 5/12 failed for files_to_issues.yml (cushion: 120s)
[DEBUG] Live API failed and no cached repository data available for files_to_issues.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:21:53.769104 -0700 PDT m=+0.062060791
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for files_to_issues.yml (handle: 186334116)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:15:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 6/12 failed for files_to_issues.yml (cushion: 150s)
[DEBUG] Live API failed and no cached repository data available for files_to_issues.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:22:00.266469 -0700 PDT m=+0.062953162
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for files_to_issues.yml (handle: 186334116)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:14:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 7/12 failed for files_to_issues.yml (cushion: 180s)
[DEBUG] Live API failed and no cached repository data available for files_to_issues.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:22:06.858464 -0700 PDT m=+0.074786919
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for files_to_issues.yml (handle: 186334116)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:14:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 8/12 failed for files_to_issues.yml (cushion: 210s)
[DEBUG] Live API failed and no cached repository data available for files_to_issues.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:22:13.407486 -0700 PDT m=+0.064564316
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for files_to_issues.yml (handle: 186334116)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:13:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 9/12 failed for files_to_issues.yml (cushion: 240s)
[DEBUG] Live API failed and no cached repository data available for files_to_issues.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:22:20.008332 -0700 PDT m=+0.083353135
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for files_to_issues.yml (handle: 186334116)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:13:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 10/12 failed for files_to_issues.yml (cushion: 270s)
[DEBUG] Live API failed and no cached repository data available for files_to_issues.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:22:26.558104 -0700 PDT m=+0.073834100
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for files_to_issues.yml (handle: 186334116)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:12:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 11/12 failed for files_to_issues.yml (cushion: 300s)
[DEBUG] Live API failed and no cached repository data available for files_to_issues.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:22:33.108132 -0700 PDT m=+0.081930985
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for files_to_issues.yml (handle: 186334116)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:12:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 12/12 failed for files_to_issues.yml (cushion: 330s)
[DEBUG] No run_id found for files_to_issues.yml, remaining pending
[DEBUG] Attempting to find run_id for issues-downsync.yml...
[DEBUG] Live API failed and no cached repository data available for issues-downsync.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:22:39.758115 -0700 PDT m=+0.077957374
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for issues-downsync.yml (handle: 187641377)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:17:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 1/12 failed for issues-downsync.yml (cushion: 0s)
[DEBUG] Live API failed and no cached repository data available for issues-downsync.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:22:42.284957 -0700 PDT m=+0.062779443
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for issues-downsync.yml (handle: 187641377)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:17:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 2/12 failed for issues-downsync.yml (cushion: 30s)
[DEBUG] Live API failed and no cached repository data available for issues-downsync.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:22:45.857862 -0700 PDT m=+0.075083190
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for issues-downsync.yml (handle: 187641377)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:16:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 3/12 failed for issues-downsync.yml (cushion: 60s)
[DEBUG] Live API failed and no cached repository data available for issues-downsync.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:22:51.373437 -0700 PDT m=+0.062985839
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for issues-downsync.yml (handle: 187641377)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:16:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 4/12 failed for issues-downsync.yml (cushion: 90s)
[DEBUG] Live API failed and no cached repository data available for issues-downsync.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:23:05.32289 -0700 PDT m=+0.063713042
* Request to https://api.github.com/...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for issues-downsync.yml (handle: 187641377)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:15:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 5/12 failed for issues-downsync.yml (cushion: 120s)
[DEBUG] Live API failed and no cached repository data available for issues-downsync.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:23:11.882408 -0700 PDT m=+0.063705619
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for issues-downsync.yml (handle: 187641377)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:15:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 6/12 failed for issues-downsync.yml (cushion: 150s)
[DEBUG] Live API failed and no cached repository data available for issues-downsync.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:23:18.457511 -0700 PDT m=+0.084641968
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for issues-downsync.yml (handle: 187641377)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:14:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 7/12 failed for issues-downsync.yml (cushion: 180s)
[DEBUG] Live API failed and no cached repository data available for issues-downsync.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:23:24.970357 -0700 PDT m=+0.067282532
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for issues-downsync.yml (handle: 187641377)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:14:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 8/12 failed for issues-downsync.yml (cushion: 210s)
[DEBUG] Live API failed and no cached repository data available for issues-downsync.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:23:31.474893 -0700 PDT m=+0.064760677
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for issues-downsync.yml (handle: 187641377)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:13:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 9/12 failed for issues-downsync.yml (cushion: 240s)
[DEBUG] Live API failed and no cached repository data available for issues-downsync.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:23:38.057404 -0700 PDT m=+0.072801334
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for issues-downsync.yml (handle: 187641377)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:13:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 10/12 failed for issues-downsync.yml (cushion: 270s)
[DEBUG] Live API failed and no cached repository data available for issues-downsync.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:23:44.657212 -0700 PDT m=+0.079268601
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for issues-downsync.yml (handle: 187641377)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:12:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 11/12 failed for issues-downsync.yml (cushion: 300s)
[DEBUG] Live API failed and no cached repository data available for issues-downsync.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:23:51.274009 -0700 PDT m=+0.063572936
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for issues-downsync.yml (handle: 187641377)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:12:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 12/12 failed for issues-downsync.yml (cushion: 330s)
[DEBUG] No run_id found for issues-downsync.yml, remaining pending
[DEBUG] Attempting to find run_id for python.yml...
[DEBUG] Live API failed and no cached repository data available for python.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:23:57.956257 -0700 PDT m=+0.074419930
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for python.yml (handle: 185372765)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:17:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 1/12 failed for python.yml (cushion: 0s)
[DEBUG] Live API failed and no cached repository data available for python.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:24:00.457095 -0700 PDT m=+0.071919934
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for python.yml (handle: 185372765)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:17:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 2/12 failed for python.yml (cushion: 30s)
[DEBUG] Live API failed and no cached repository data available for python.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:24:04.159395 -0700 PDT m=+0.064543123
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for python.yml (handle: 185372765)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:16:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 3/12 failed for python.yml (cushion: 60s)
[DEBUG] Live API failed and no cached repository data available for python.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:24:09.717386 -0700 PDT m=+0.063806648
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for python.yml (handle: 185372765)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:16:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 4/12 failed for python.yml (cushion: 90s)
[DEBUG] Live API failed and no cached repository data available for python.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:24:19.256774 -0700 PDT m=+0.081648289
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for python.yml (handle: 185372765)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:15:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 5/12 failed for python.yml (cushion: 120s)
[DEBUG] Live API failed and no cached repository data available for python.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:24:25.833252 -0700 PDT m=+0.064174317
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for python.yml (handle: 185372765)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:15:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 6/12 failed for python.yml (cushion: 150s)
[DEBUG] Live API failed and no cached repository data available for python.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:24:32.334404 -0700 PDT m=+0.062804959
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for python.yml (handle: 185372765)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:14:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 7/12 failed for python.yml (cushion: 180s)
[DEBUG] Live API failed and no cached repository data available for python.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:24:38.879074 -0700 PDT m=+0.063584794
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for python.yml (handle: 185372765)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:14:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 8/12 failed for python.yml (cushion: 210s)
[DEBUG] Live API failed and no cached repository data available for python.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:24:45.405533 -0700 PDT m=+0.063470980
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for python.yml (handle: 185372765)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:13:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 9/12 failed for python.yml (cushion: 240s)
[DEBUG] Live API failed and no cached repository data available for python.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:24:51.956391 -0700 PDT m=+0.074337580
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for python.yml (handle: 185372765)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:13:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 10/12 failed for python.yml (cushion: 270s)
[DEBUG] Live API failed and no cached repository data available for python.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:24:58.521247 -0700 PDT m=+0.061548776
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for python.yml (handle: 185372765)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:12:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 11/12 failed for python.yml (cushion: 300s)
[DEBUG] Live API failed and no cached repository data available for python.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:25:05.156249 -0700 PDT m=+0.078288248
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for python.yml (handle: 185372765)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:12:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 12/12 failed for python.yml (cushion: 330s)
[DEBUG] No run_id found for python.yml, remaining pending
[DEBUG] Attempting to find run_id for release-drafter.yml...
[DEBUG] Live API failed and no cached repository data available for release-drafter.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:25:11.755356 -0700 PDT m=+0.070726473
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for release-drafter.yml (handle: 185372766)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:17:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 1/12 failed for release-drafter.yml (cushion: 0s)
[DEBUG] Live API failed and no cached repository data available for release-drafter.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:25:14.255435 -0700 PDT m=+0.081086277
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for release-drafter.yml (handle: 185372766)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:17:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 2/12 failed for release-drafter.yml (cushion: 30s)
[DEBUG] Live API failed and no cached repository data available for release-drafter.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:25:17.806446 -0700 PDT m=+0.062943298
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for release-drafter.yml (handle: 185372766)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:16:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 3/12 failed for release-drafter.yml (cushion: 60s)
[DEBUG] Live API failed and no cached repository data available for release-drafter.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:25:23.415611 -0700 PDT m=+0.063180444
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for release-drafter.yml (handle: 185372766)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:16:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 4/12 failed for release-drafter.yml (cushion: 90s)
[DEBUG] Live API failed and no cached repository data available for release-drafter.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:25:33.005845 -0700 PDT m=+0.079366468
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for release-drafter.yml (handle: 185372766)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:15:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 5/12 failed for release-drafter.yml (cushion: 120s)
[DEBUG] Live API failed and no cached repository data available for release-drafter.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:25:40.00583 -0700 PDT m=+0.084805886
* Request to https://api.github.com/...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for release-drafter.yml (handle: 185372766)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:15:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 6/12 failed for release-drafter.yml (cushion: 150s)
[DEBUG] Live API failed and no cached repository data available for release-drafter.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:25:46.906832 -0700 PDT m=+0.084761999
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for release-drafter.yml (handle: 185372766)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:14:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 7/12 failed for release-drafter.yml (cushion: 180s)
[DEBUG] Live API failed and no cached repository data available for release-drafter.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:25:53.43101 -0700 PDT m=+0.061165360
* Request to https://api.github.com/...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for release-drafter.yml (handle: 185372766)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:14:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 8/12 failed for release-drafter.yml (cushion: 210s)
[DEBUG] Live API failed and no cached repository data available for release-drafter.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:26:04.322039 -0700 PDT m=+0.062607761
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for release-drafter.yml (handle: 185372766)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:13:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 9/12 failed for release-drafter.yml (cushion: 240s)
[DEBUG] Live API failed and no cached repository data available for release-drafter.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:26:10.854547 -0700 PDT m=+0.067135916
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for release-drafter.yml (handle: 185372766)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:13:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 10/12 failed for release-drafter.yml (cushion: 270s)
[DEBUG] Live API failed and no cached repository data available for release-drafter.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:26:17.420852 -0700 PDT m=+0.062683650
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for release-drafter.yml (handle: 185372766)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:12:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 11/12 failed for release-drafter.yml (cushion: 300s)
[DEBUG] Live API failed and no cached repository data available for release-drafter.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:26:23.955265 -0700 PDT m=+0.071581286
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for release-drafter.yml (handle: 185372766)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:12:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 12/12 failed for release-drafter.yml (cushion: 330s)
[DEBUG] No run_id found for release-drafter.yml, remaining pending
[DEBUG] Attempting to find run_id for shared-indexes-smoke.yml...
[DEBUG] Live API failed and no cached repository data available for shared-indexes-smoke.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:26:30.574843 -0700 PDT m=+0.064528341
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for shared-indexes-smoke.yml (handle: 187565896)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:17:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 1/12 failed for shared-indexes-smoke.yml (cushion: 0s)
[DEBUG] Live API failed and no cached repository data available for shared-indexes-smoke.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:26:33.155204 -0700 PDT m=+0.082606155
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for shared-indexes-smoke.yml (handle: 187565896)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:17:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 2/12 failed for shared-indexes-smoke.yml (cushion: 30s)
[DEBUG] Live API failed and no cached repository data available for shared-indexes-smoke.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:26:41.104107 -0700 PDT m=+0.071609323
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for shared-indexes-smoke.yml (handle: 187565896)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:16:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 3/12 failed for shared-indexes-smoke.yml (cushion: 60s)
[DEBUG] Live API failed and no cached repository data available for shared-indexes-smoke.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:26:46.632854 -0700 PDT m=+0.061850832
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for shared-indexes-smoke.yml (handle: 187565896)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:16:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 4/12 failed for shared-indexes-smoke.yml (cushion: 90s)
[DEBUG] Live API failed and no cached repository data available for shared-indexes-smoke.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:26:56.156037 -0700 PDT m=+0.064806173
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for shared-indexes-smoke.yml (handle: 187565896)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:15:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 5/12 failed for shared-indexes-smoke.yml (cushion: 120s)
[DEBUG] Live API failed and no cached repository data available for shared-indexes-smoke.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:27:02.868811 -0700 PDT m=+0.073983768
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for shared-indexes-smoke.yml (handle: 187565896)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:15:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 6/12 failed for shared-indexes-smoke.yml (cushion: 150s)
[DEBUG] Live API failed and no cached repository data available for shared-indexes-smoke.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:27:09.654228 -0700 PDT m=+0.079779158
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for shared-indexes-smoke.yml (handle: 187565896)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:14:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 7/12 failed for shared-indexes-smoke.yml (cushion: 180s)
[DEBUG] Live API failed and no cached repository data available for shared-indexes-smoke.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:27:16.209264 -0700 PDT m=+0.062687066
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for shared-indexes-smoke.yml (handle: 187565896)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:14:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 8/12 failed for shared-indexes-smoke.yml (cushion: 210s)
[DEBUG] Live API failed and no cached repository data available for shared-indexes-smoke.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:27:22.804312 -0700 PDT m=+0.075736607
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for shared-indexes-smoke.yml (handle: 187565896)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:13:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 9/12 failed for shared-indexes-smoke.yml (cushion: 240s)
[DEBUG] Live API failed and no cached repository data available for shared-indexes-smoke.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:27:29.379433 -0700 PDT m=+0.064956609
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for shared-indexes-smoke.yml (handle: 187565896)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:13:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 10/12 failed for shared-indexes-smoke.yml (cushion: 270s)
[DEBUG] Live API failed and no cached repository data available for shared-indexes-smoke.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:27:35.954526 -0700 PDT m=+0.082991501
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for shared-indexes-smoke.yml (handle: 187565896)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:12:49Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 11/12 failed for shared-indexes-smoke.yml (cushion: 300s)
[DEBUG] Live API failed and no cached repository data available for shared-indexes-smoke.yml
[DEBUG] Repository-wide API call failed and no cached data available
[DEBUG] Repo API error:    [DEBUG] safe_gh_api: attempt 1/3 for repos/mhold3n/CamProV5/actions/runs
[DEBUG] safe_gh_api: API call failed (exit_code=1) on attempt 1: * Request at 2025-09-14 23:27:46.823802 -0700 PDT m=+0.062914748
* Request to https://api.github.com...
  [DEBUG] Non-retryable error or max attempts reached for repos/mhold3n/CamProV5/actions/runs
  [DEBUG] safe_gh_api: all attempts failed for repos/mhold3n/CamProV5/actions/runs, returning empty

Repo API call failed
[DEBUG] Live workflow API failed and no cached workflow data available for shared-indexes-smoke.yml (handle: 187565896)
[DEBUG] Workflow-specific API failed and no cached data available
[DEBUG] Cushion timestamp: 2025-09-15T06:12:19Z
[DEBUG] Raw runs response length:
[DEBUG] Recent runs found:
[DEBUG] Attempt 12/12 failed for shared-indexes-smoke.yml (cushion: 330s)
[DEBUG] No run_id found for shared-indexes-smoke.yml, remaining pending

Collecting results...

=== Workflow: ci.yml (type=GENERAL_WORKFLOW) ===
Result: DISPATCH_FAILED
Error reason: no_workflow_dispatch

=== Workflow: codeql.yml (type=GENERAL_WORKFLOW) ===
Result: DISPATCH_FAILED
Error reason: no_workflow_dispatch

=== Workflow: dependency-review.yml (type=GENERAL_WORKFLOW) ===
Result: DISPATCH_FAILED
Error reason: no_workflow_dispatch

=== Workflow: files-to-issues.yml (type=GENERAL_WORKFLOW) ===
Result: TIMED_OUT (no run appeared)
Detail: No run_id discovered since 2025-09-15T06:17:49Z

=== Workflow: files_to_issues.yml (type=GENERAL_WORKFLOW) ===
Result: TIMED_OUT (no run appeared)
Detail: No run_id discovered since 2025-09-15T06:17:49Z

=== Workflow: guard-shared-indexes.yml (type=GENERAL_WORKFLOW) ===
Result: DISPATCH_FAILED
Error reason: no_workflow_dispatch

=== Workflow: issues-downsync.yml (type=GENERAL_WORKFLOW) ===
Result: TIMED_OUT (no run appeared)
Detail: No run_id discovered since 2025-09-15T06:17:49Z

=== Workflow: labeler.yml (type=GENERAL_WORKFLOW) ===
Result: DISPATCH_FAILED
Error reason: no_workflow_dispatch

=== Workflow: pr-title-lint.yml (type=GENERAL_WORKFLOW) ===
Result: DISPATCH_FAILED
Error reason: no_workflow_dispatch

=== Workflow: python-ci.yml (type=GENERAL_WORKFLOW) ===
Result: DISPATCH_FAILED
Error reason: no_workflow_dispatch

=== Workflow: python.yml (type=GENERAL_WORKFLOW) ===
Result: TIMED_OUT (no run appeared)
Detail: No run_id discovered since 2025-09-15T06:17:49Z

=== Workflow: release-drafter.yml (type=GENERAL_WORKFLOW) ===
Result: TIMED_OUT (no run appeared)
Detail: No run_id discovered since 2025-09-15T06:17:49Z

=== Workflow: release.yml (type=GENERAL_WORKFLOW) ===
Result: DISPATCH_FAILED
Error reason: no_workflow_dispatch

=== Workflow: shared-indexes-smoke.yml (type=GENERAL_WORKFLOW) ===
Result: TIMED_OUT (no run appeared)
Detail: No run_id discovered since 2025-09-15T06:17:49Z

=== Workflow: todos_to_issues.yml (type=GENERAL_WORKFLOW) ===
Result: DISPATCH_FAILED
Error reason: no_workflow_dispatch

One or more workflows did not resolve successfully.
(base) maxholden@MacBookPro CamProV5 % 