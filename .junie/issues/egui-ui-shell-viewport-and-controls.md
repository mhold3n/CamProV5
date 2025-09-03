---
title: "[Junie] egui UI shell: viewport, panels, and session controls (ui_app)"
labels: [junie:ready, p0]
intent: implement
---

## Context
Provide the Rust application shell with a 3D viewport wired to render_core, side panels, and session controls (play/pause/seek/step). Display FPS/latency HUD and support field/overlay toggles. Handle solver divergence with an error surface and rollback action.

## Acceptance Criteria
- ui_app launches a window with:
  - A wgpu-powered viewport via render_core.
  - Controls for play/pause/seek/step; FPS and latency HUD.
  - Field/overlay toggles (displacement, von Mises) persisted per session.
  - Error surface for solver divergence and quick rollback.
- Smooth 60 FPS on demo mesh with interpolation when solver dt > render dt.