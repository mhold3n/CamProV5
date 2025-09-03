---
title: "[Junie] Probes panel and plotting from frame stream"
labels: [junie:ready, p1]
intent: implement
---

## Context
Implement a probes panel whose data derives from the same frame stream as the renderer to ensure synchronization with visuals. Decouple plot update cadence from render FPS and persist probe selections in session state.

## Acceptance Criteria
- Probes panel displays selected DOFs/actuator loads sourced from frame stream.
- Plot update cadence decoupled from render FPS; smooth and responsive.
- Probe selections persisted per session and restored on reopen.
- Unit tests for probe sampling and resampling when render rate changes.