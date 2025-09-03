---
title: "[Junie] Picking and BVH for hit‑testing (render_core)"
labels: [junie:ready, p1]
intent: implement
---

## Context
Implement accurate selection mapped to stable topology handles (part_id, vertex/triangle id) with minimal per‑frame cost. Build a BVH once per topology version and refit as needed. Expose a ray‑triangle picking API returning stable handles.

## Acceptance Criteria
- BVH build/refit strategy implemented: build on topology changes; refit if necessary.
- Ray‑triangle picking returns (part_id, triangle_id and/or vertex_id) with tests.
- Unit tests and golden tests verify picking accuracy on sample meshes.
- Public API in render_core for picking integrates with ui_app selection.