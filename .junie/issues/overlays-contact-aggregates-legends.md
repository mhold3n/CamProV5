---
title: "[Junie] Overlays: contact patch, per‑part aggregates, legends"
labels: [junie:ready, p1]
intent: implement
---

## Context
Provide essential engineering overlays for stress/contact visualization in the Rust UI. Render contact patch geometry when present, expose per‑part aggregates for fast legends, and support auto/manual color map ranges.

## Acceptance Criteria
- Contact patch geometry (polylines/meshes) rendered with toggles in the UI.
- Per‑part aggregates (min/max stress, RMS displacement) displayed with legends.
- Color map range supports auto and manual modes; persisted per session.
- Golden image tests verify overlays on sample meshes; docs note performance characteristics.