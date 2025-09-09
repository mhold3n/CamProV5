# Tight, safe, and cost-aware implementation (aligned to your policy)

Below is a *finalized* set of workflow edits that bake in your review: dual `main/master` support, optional merge-queue hooks (only if enabled), minimal permissions, concurrency, path filters, draft-PR guards, and stable job names for required checks.

---

## A) Core CI (multi-lang) — PRs + feature/fix pushes; optional merge queue

```yaml
# .github/workflows/ci.yml
name: CI

on:
  pull_request:
    branches: [ main, master ]
    paths-ignore:
      - '.junie/**'
      - 'docs/**'
      - '**/*.md'
  # Enable ONLY if you turn on Merge Queue. Otherwise omit.
  # merge_group: {}
  push:
    branches:
      - 'feature/**'
      - 'fix/**'
      # - 'chore/**'       # optional
      # - 'experiment/**' # optional
    paths-ignore:
      - '.junie/**'
      - 'docs/**'
      - '**/*.md'

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true

jobs:
  jvm-desktop:
    name: CI / jvm-desktop
    if: github.event_name != 'pull_request' || github.event.pull_request.draft == false
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
      - name: Ensure Gradle wrapper is executable
        run: chmod +x ./gradlew
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '17'
      - uses: gradle/actions/setup-gradle@v3   # includes caching & configuration-cache support
      - run: ./gradlew test --stacktrace
      - run: ./gradlew :desktop:ktlintCheck
  rust-fea-engine:
    name: CI / rust-fea-engine
    if: github.event_name != 'pull_request' || github.event.pull_request.draft == false
    runs-on: ubuntu-latest
    timeout-minutes: 30
    defaults:
      run:
        working-directory: path/to/your/crate
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - name: Cache Cargo registry + target
        uses: actions/cache@v4
        with:
          path: |
            ~/.cargo/registry
            ~/.cargo/git
            path/to/your/crate/target
          key: cargo-${{ runner.os }}-${{ hashFiles('path/to/your/crate/Cargo.lock') }}
          restore-keys: |
            cargo-${{ runner.os }}-
      - run: cargo build --locked --all-targets
      - run: cargo test  --locked --all
      - run: cargo clippy -- -D warnings
```

Why these switches matter: required checks must run on PRs; add `merge_group` **only if** you enable Merge Queue, because checks must run on the queue’s synthetic branch to count as required. ([GitHub Docs][1])
Gradle action handles caching/configuration-cache; Cargo caching cuts minutes; `paths-ignore` + draft guards save spend. ([Gradle Documentation][2], [Stack Overflow][3])

---

## B) Python matrix — Ubuntu-only to start; same policy switches

```yaml
# .github/workflows/python-ci.yml
name: Python CI

on:
  pull_request:
    branches: [ main, master ]
    paths-ignore: [ '.junie/**', 'docs/**', '**/*.md' ]
  # merge_group: {}    # ONLY if Merge Queue is enabled and you’ll require this check
  push:
    branches: [ 'feature/**', 'fix/**' ]
    paths-ignore: [ '.junie/**', 'docs/**', '**/*.md' ]

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true

jobs:
  test:
    name: CI / python
    if: github.event_name != 'pull_request' || github.event.pull_request.draft == false
    runs-on: ubuntu-latest
    timeout-minutes: 30
    strategy:
      matrix:
        python-version: [ '3.12' ]   # expand later if needed
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'               # built-in pip cache
      - run: python -m pip install -U pip
      - if: hashFiles('requirements.txt') != ''
        run: pip install -r requirements.txt
      - run: pytest -q               # add -n auto if you adopt pytest-xdist
```

Built-in pip cache is supported directly in `setup-python`. Start Ubuntu-only unless you have OS-specific code paths. ([GitHub][4], [The GitHub Blog][5])

---

## C) CodeQL — pick one (required vs. non-required)

**If you will mark CodeQL as a *required* status** (and optionally use Merge Queue), include `merge_group`:

```yaml
# .github/workflows/codeql.yml
name: CodeQL
on:
  pull_request: { branches: [ main, master ] }
  # merge_group: {}    # include only if using Merge Queue AND CodeQL is required
  schedule:
    - cron: '0 3 * * 1'
permissions:
  contents: read
  security-events: write
  actions: read
# ... rest (init/analyze) unchanged ...
```

**If CodeQL is *not* required**, keep only PR + weekly cron (no `push`) to avoid duplicate runs: same as above **without** `merge_group`. Default CodeQL templates already scan weekly on `schedule`. ([GitHub Docs][6])

---

## D) Dependency Review — PR-only

```yaml
# .github/workflows/dependency-review.yml
name: Dependency Review
on: { pull_request: {} }
permissions: { contents: read }
jobs:
  review:
    name: Dependency Review
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/dependency-review-action@v4
```

This blocks PRs that introduce known-vulnerable/invalid-license deps; use as a required check. ([GitHub Docs][7], [GitHub][8])

---

## E) PR Title Lint — automatic, PR events only

```yaml
# .github/workflows/pr-title-lint.yml
name: PR Title Lint
on:
  pull_request:
    types: [ opened, edited, synchronize, reopened ]
permissions:
  pull-requests: read
jobs:
  lint:
    name: PR Title Lint
    runs-on: ubuntu-latest
    steps:
      - uses: amannn/action-semantic-pull-request@v5
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          types: |
            feat
            fix
            docs
            refactor
            test
            chore
          requireScope: false
```

If you later make this a *required* check and enable Merge Queue, mirror the trigger with `merge_group` too. ([GitHub Docs][9])

---

## F) Files → Issues (upsync) — never on `main` or bot branch

```yaml
# .github/workflows/files-to-issues.yml
name: Mirror Repo Files → GitHub Issues
on:
  push:
    branches-ignore: [ main, bot/issue-sync ]
    paths:
      - '.junie/issues/**'
      - '.junie/comments/**'
  workflow_dispatch:

permissions:
  contents: read
  issues: write

jobs:
  upsync:
    name: Files → Issues
    if: >
      github.actor != 'github-actions[bot]' &&
      !contains(github.event.head_commit.message, '[junie-mirror]')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      # ... your existing script that creates/updates issues ...
```

Pushes created with the repo `GITHUB_TOKEN` **don’t** trigger new workflows (prevents loops) — which your mirroring relies on. ([GitHub Docs][10], [Stack Overflow][11])

---

## G) Issues → Files (downsync) — ensure bot branch exists, write-only

```yaml
# .github/workflows/issues-downsync.yml
name: Issues → Files (bot branch)
on:
  schedule: [ { cron: '*/30 * * * *' } ]
  issues:
    types: [ opened, edited, closed, reopened, labeled, unlabeled ]
  issue_comment:
    types: [ created, edited, deleted ]
  workflow_dispatch:

permissions:
  contents: write

jobs:
  downsync:
    name: Issues → Files
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Ensure bot branch exists
        run: |
          if ! git ls-remote --exit-code --heads origin bot/issue-sync; then
            git switch -c bot/issue-sync
            git push -u origin bot/issue-sync
          else
            git fetch origin bot/issue-sync:bot/issue-sync
            git switch bot/issue-sync
          fi
      - name: Export issues/comments to files
        run: |
          sudo apt-get update && sudo apt-get install -y jq
          mkdir -p .junie/issues .junie/comments
          # your gh/jq dump here…
      - uses: stefanzweifel/git-auto-commit-action@v6
        with:
          branch: bot/issue-sync
          commit_message: "chore(junie-mirror): downsync"
```

(Downsync uses `GITHUB_TOKEN`; per GitHub behavior, those pushes won’t retrigger other workflows.) ([GitHub Docs][10])

---

## H) Guard checks — scoped to relevant paths only (noise/cost reducer)

```yaml
# .github/workflows/guard-shared-indexes.yml
name: Guard Shared Indexes
on:
  pull_request:
    branches: [ main, master ]
    paths:
      - 'shared-index/**'
      - 'scripts/shared-index/**'
      - 'scripts/ci/**'
  push:
    branches: [ main, master ]
    paths:
      - 'shared-index/**'
      - 'scripts/shared-index/**'
      - 'scripts/ci/**'

permissions: { contents: read }

jobs:
  guard:
    name: Guard Shared Indexes
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: ./scripts/ci/check-shared-indexes.sh
```

---

## I) Required checks & rules (stable job names)

| Check (job name)         | Required on `main` | Notes                                                                                    |
| ------------------------ | -----------------: | ---------------------------------------------------------------------------------------- |
| **CI / jvm-desktop**     |                  ✅ | Gradle test job                                                                          |
| **CI / rust-fea-engine** |                  ✅ | Rust build/test/clippy                                                                   |
| **CI / python**          |                  ✅ | Python matrix                                                                            |
| **Dependency Review**    |                  ✅ | PR-only check                                                                            |
| **CodeQL**               |              ✅ / ❌ | ✅ only if you added it as required *and* (when using Merge Queue) included `merge_group` |
| **PR Title Lint**        |           optional | Make required if you want clean commit history                                           |

Configure these as *required status checks* under branch protection/rulesets. If you enable **Merge Queue**, you must add `merge_group` to every workflow that reports a required check (or the queue cannot collect a result). ([GitHub Docs][12])

---

## J) Cost & reliability hardening (small but high-leverage)

* **Timeouts** on heavy jobs (`timeout-minutes: 30`) to avoid hung bills.
* **Caching**: Gradle action (build & config cache), `setup-python` (pip), Cargo cache. ([Gradle Documentation][2], [GitHub][4], [Stack Overflow][3])
* **Bash safety** for multi-line scripts: `set -euo pipefail`.
* **Draft PR skip**: job-level `if: github.event_name != 'pull_request' || github.event.pull_request.draft == false` (field is present on PR payloads). ([GitHub][13], [GitHub Docs][14])

---

## K) Post-merge verification (fast)

1. Push to `feature/*`: three CI jobs run; dependency review waits for a PR.
2. Open PR → `main`: CI + Dependency Review (+ CodeQL if configured) run; draft PRs don’t run heavy jobs.
3. If using Merge Queue: add PR to queue → observe checks under `merge_group`.
4. Push `.junie/issues/*` on feature branch: upsync runs; pushing to `main` or `bot/issue-sync` does **not**.
5. Downsync cron writes to `bot/issue-sync` (doesn’t loop new workflows). ([GitHub Docs][10])
