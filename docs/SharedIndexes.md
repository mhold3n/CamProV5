# JetBrains Shared Indexes — Setup, Update, and Guardrails

This document explains how CamProV5 manages JetBrains Shared Indexes using repository-local links to content stored outside the repository (Option A).

## Concepts
- INSTALL_ROOT: the folder outside the repo that contains the actual shared indexes. By default it is the parent folder named `github` (e.g., .../Documents/github).
- REPO_ROOT: your cloned CamProV5 project directory.
- Managed directories:
  - `.shared-indexes`
  - `ij-shared-indexes-tool-data`
  - `ij-shared-indexes-tool-cli`

The repository contains links (symlinks or junctions on Windows) pointing to these directories under INSTALL_ROOT.

## Post-clone setup

macOS/Linux:
```
bash scripts/setup-shared-indexes.sh --download-manifest .junie/config/shared-indexes.yaml --yes
```

Windows (PowerShell):
```
pwsh -File scripts/setup-shared-indexes.ps1 -DownloadManifest .junie/config/shared-indexes.yaml -Yes
```

Flags (bash/PowerShell equivalents):
- `--install-root` / `-InstallRoot`: override INSTALL_ROOT path
- `--create-missing` / `-CreateMissing`: create empty targets if missing
- `--download-manifest` / `-DownloadManifest`: YAML/JSON manifest with assets to download and extract
- `--verify` / `-Verify`: dereference the links and probe-read a small file if present
- `--yes` / `-Yes`: assume yes for confirmations
- `--quiet` / `-Quiet`: reduce output
- `--untrack` / `-Untrack`: run `git rm -r --cached` on protected folders (guarded)

Environment overrides:
- `SHARED_INDEXES_MANIFEST` — default manifest path if flags not provided

## Manifest format (YAML)
`.junie/config/shared-indexes.yaml`:
```yaml
installRootName: github
expectedFiles:
  .shared-indexes:
    - index.info
  ij-shared-indexes-tool-cli:
    - bin/ijSharedIndexesTool
assets:
  - dir: .shared-indexes
    url: https://example.com/shared-indexes/sample-linux-x64.zip
    sha256: 0123...cdef
  - dir: ij-shared-indexes-tool-data
    url: https://example.com/shared-indexes/tool-data.zip
    sha256: 0123...cdef
  - dir: ij-shared-indexes-tool-cli
    url: https://example.com/shared-indexes/cli.zip
    sha256: 0123...cdef
```
JSON with the same structure is also supported.

## Updating to a new version (atomic)

macOS/Linux:
```
bash scripts/update-shared-indexes.sh --version v2025.09.08 --manifest .junie/config/shared-indexes.yaml --set-current --yes
```

Windows:
```
pwsh -File scripts/update-shared-indexes.ps1 -Version v2025.09.08 -Manifest .junie/config/shared-indexes.yaml -SetCurrent -Yes
```

What it does:
- Downloads assets to a temp directory under INSTALL_ROOT, verifies checksums
- Extracts into versioned directories: `<dir>-<version>`
- Switches the stable alias `<dir>` to point to the new version (symlink or junction)
- Leaves previous versions available for rollback

Rollback: If validation fails, the scripts keep the previous alias and leave artifacts under `.failed-<timestamp>`. You can add `--rollback-on-fail` (bash) or `-RollbackOnFail` (PowerShell) to ensure that if an alias switch fails mid-way, all previously updated aliases are restored transactionally.

Integrity and verification:
- Checksum precedence: CLI flag > manifest `sha256` > sidecar `.sha256` file next to the archive (auto-detected).
- Optional GPG: if an `.asc` signature file is present and `gpg` is installed, the scripts verify signatures and abort on failure.

Manifest templating and platform selection:
- The manifest supports `platforms` with per-OS assets and URL templates containing `{{channel}}` and `{{version}}`.
- Channel is selected from `$SHARED_INDEXES_CHANNEL` (default `stable`).
- Version token defaults to `--version` or `$SHARED_INDEXES_VERSION`.

CI and helpers:
- CI smoke workflow `.github/workflows/shared-indexes-smoke.yml` runs tiny end-to-end checks on Ubuntu and Windows.
- Developer helper scripts:
  - `scripts/dev/check-idea-shared-indexes.sh`
  - `scripts/dev/check-idea-shared-indexes.ps1`
  These print alias targets and grep IDEA logs for "Shared indexes" hints.

## Guardrails
- CI guard workflow `.github/workflows/guard-shared-indexes.yml` fails if PRs try to add files in protected directories.
- Optional pre-commit hook templates are provided:
  - `.githooks/prevent-shared-indexes.sh`
  - `.githooks/prevent-shared-indexes.ps1`
Install with:
```
git config core.hooksPath .githooks
```

## Troubleshooting
- Windows symlinks require Developer Mode or admin; scripts fall back to directory junctions.
- Ensure tools for extraction are present: `unzip`, `tar` (with gzip), optional `zstd`.
- If checksum mismatch occurs, the scripts abort before extraction.
- If IDE caches old paths, use “Invalidate Caches / Restart”.
