# CamProV5 — Junie Project Guidelines (GitHub‑Centered)

Purpose
- Make GitHub Issues the primary interface for planning and prompting Junie.
- Keep a reliable two‑way mirror between GitHub Issues and the repository’s .junie directory.
- Reduce direct chat prompts in favor of concise prompts like: “fix issue #37”.

Scope
- Applies to all modules: Kotlin/Compose Desktop (desktop), Android (android), Rust crates (camprofw/rust), Python tools (campro), and C++ (cpp).
- This document explains how Junie should work, how the mirrors function, build/test expectations, and daily operations.

1. Source of truth: GitHub Issues
- All work items must be expressed as GitHub Issues (or authored locally as .junie/issues/*.md which will create Issues on push).
- Prefer prompting via Issues: titles should be concise; the body should include Context and Acceptance Criteria.
- Use “Fixes #<issue>” in PR descriptions to auto‑close issues upon merge.

2. Two‑way mirroring (files ↔ issues)
- Upsync (files → issues): .github/workflows/files_to_issues.yml
  - Trigger: push that touches .junie/issues/** or .junie/comments/**
  - Behavior: creates or updates Issues from .junie markdown files via .github/scripts/junie_files_to_issues.py
  - Auth: uses GITHUB_TOKEN (or GH_TOKEN secret if configured). If your org restricts GITHUB_TOKEN for Issues, add a fine‑grained PAT secret GH_TOKEN with Issues/Contents RW and the workflow will pick it up.
- Downsync (issues → files): .github/workflows/issues_to_files.yml
  - Triggers: issue and comment events, scheduled every 30 minutes, and manual dispatch
  - Behavior: writes numbered mirrors to .junie/issues/<number>.md and .junie/comments/<number>/** on branch bot/issue-sync
  - Merge policy: Regularly merge bot/issue-sync into the default branch so Junie’s local view (.junie) stays current. Consider enabling an auto‑PR for bot/issue-sync if desired.
- Loop prevention: Downsync commits are marked with [junie-mirror] and are ignored by upsync.

3. Issue authoring conventions
- Structure
  - Title: [Junie] <short task> or a clear descriptive title
  - Labels: use product labels as needed; operational labels below guide Junie’s state
  - Body sections:
    - Context: code links/paths, constraints, relevant workflows
    - Acceptance Criteria: explicit, testable outcomes
    - Intent (optional): implement | fix | refactor | test | docs
- Local .junie creation (alternative to GH UI)
  - Create .junie/issues/<slug>.md without an issue: field; include front matter fields like title, labels, intent
  - Push to trigger upsync; watch for “Created issue #NNN …” in the workflow logs

4. Operational labels (state machine)
- junie:ready — triaged and ready for Junie to pick up
- junie:working — Junie is actively implementing
- junie:needs-info — Junie is blocked and awaiting input
- junie:review — PR opened and awaiting human review
- junie:mirror — applied automatically to the bot/issue-sync PR (optional if auto‑PR is enabled)
- Optional priority labels: p0, p1, p2

5. TODO discipline in code
- When an Issue exists, reference it in code comments to avoid duplicates and enable auto‑close:
  - // TODO(#123): Implement add tab functionality …
- The TODOs → Issues action (.github/workflows/todos_to_issues.yml) only creates issues for newly introduced or modified TODO/FIXME lines. Prefer #‑referenced TODOs once an issue number exists.

6. Junie’s working protocol
- Intake
  - Junie polls the mirrored .junie/issues/*.md for items labeled junie:ready (after you merge bot/issue-sync).
- Planning & execution
  - Junie updates the Issue with a short plan (checklist) and moves label to junie:working.
  - Junie makes minimal code changes to satisfy acceptance criteria, referencing the issue in commits.
- PR & closure
  - Junie opens a PR with “Fixes #<issue>” where appropriate, switching label to junie:review.
  - On merge, Issue closes; downsync updates .junie. Junie may remove resolved TODO(#issue) lines.

7. Builds and tests — expectations for Junie
- General
  - Keep patches minimal; avoid touching unrelated modules.
  - Provide clear commit messages: type(scope): subject (refs|fixes #<issue>)
- When to run builds/tests locally (Junie)
  - Kotlin Desktop: ./gradlew :desktop:build and :desktop:test
  - Rust (if touched): cargo build && cargo test in affected crate(s)
  - Python (if touched): pip install -r requirements.txt && pytest (if tests/ exists)
  - C++ (if touched): build only if CI requires it; otherwise rely on existing CMake/jobs if present
- CI posture
  - The repository has dedicated jobs for desktop (Gradle) and Rust crates, and matrix Python tests. If unrelated modules are failing, Junie should still submit focused PRs limited to the affected paths. Reviewers can choose to override or adjust CI gating as needed.

8. Daily operations for maintainers
- Triage new Issues; add junie:ready to those suitable for Junie.
- Ensure bot/issue-sync is merged (or merge the auto‑PR if enabled) to keep .junie mirrors current.
- Review Junie’s PRs promptly; leave comments (downsync mirrors comments to .junie/comments/<issue>). Merge when acceptable.
- Convert ad‑hoc requests into Issues. If it’s not an Issue, it doesn’t exist.

9. Troubleshooting mirroring
- Nothing happens after push
  - Ensure the push modified .junie/issues/** or .junie/comments/** (for upsync), or that a TODO/FIXME line changed (for TODOs → Issues).
- 401/403 creating Issues
  - Use a GH fine‑grained PAT secret GH_TOKEN with Issues/Contents RW and ensure workflows export it as GITHUB_TOKEN.
- Conflict warning (updated_at newer on GitHub)
  - Merge the latest downsync (bot/issue-sync) first, then reapply local edits to the numbered .junie file and push again.

10. Example prompts (issue‑first)
- “fix issue #37” — Junie reads the mirrored 37.md, implements the fix, opens a PR with “Fixes #37”.
- “implement acceptance criteria in #45 for tab reordering” — Junie scopes to the code mentioned in the issue body and patches minimally.
- “add tests for #52” — Junie adds tests aligned with the issue’s acceptance criteria and updates CI as needed.

Appendix A — Repository overview
- desktop: Kotlin/Compose Desktop app (primary UI). Build: ./gradlew :desktop:build; Run: ./gradlew :desktop:run
- android: Android module. Build: ./gradlew :android:assembleDebug
- camprofw/rust/fea-engine: Rust engine crates. Build/Test: cargo build && cargo test
- campro, layouts: Python tools/packages. Install/test via requirements.txt and pytest
- cpp: Native components. Built where applicable by CI or per‑module scripts

Appendix B — Suggested improvements (non‑blocking)
- Add .github/ISSUE_TEMPLATE/junie-task.yml to standardize prompts (Context, Acceptance Criteria, Intent).
- Add operational labels in the repository (junie:ready, junie:working, junie:needs-info, junie:review, junie:mirror, p0/p1).
- Optional: In issues_to_files.yml, auto‑open a PR from bot/issue-sync to the default branch using peter-evans/create-pull-request@v6.

Version
- Last updated: 2025-09-03 14:08 local time.
