---
title: "[Junie] Deterministic capture/replay and export"
labels: [junie:ready, p0]
intent: implement
---

## Context
Provide deterministic captures to reproduce animations and enable reliable still/video exports. Record capture artifacts and support replay that yields identical state_hash and per‑frame content hashes. Export still frames and short clips.

## Acceptance Criteria
- Session API supports capture_begin/capture_end; capture artifacts recorded and discoverable.
- Replay mode yields identical state_hash and per‑frame content hashes compared to capture.
- Export still images and short MP4/WebM clips; command‑line and UI flows documented.
- Tests verify hash equality on replay and basic export integrity.