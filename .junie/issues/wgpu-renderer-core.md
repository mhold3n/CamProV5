---
title: "[Junie] wgpu renderer core: mesh upload, dynamic buffers, colormap textures"
labels: [junie:ready, p0]
intent: implement
---

## Context
Build render_core for high‑throughput vertex uploads and scalar field color mapping. Provide static topology uploads (rebuild on topo_version changes), dynamic displaced vertex buffers with double‑buffering or persistent mapping, scalar field upload and color maps, and a basic timing API.

## Acceptance Criteria
- render_core provides:
  - Static topology upload path; rebuilds GPU buffers on topo_version change.
  - Dynamic displaced vertex buffers with double‑buffering or persistent mapping.
  - Scalar field upload path (e.g., von Mises) and colormap textures; hooks for legends.
  - Frame timing API to target 60–144 FPS.
- Benchmarks with synthetic data demonstrate ≥60 FPS on medium meshes.