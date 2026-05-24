---
name: sec-threat-model
description: "Produce or refresh a STRIDE-style threat model for the SWA + VM API + Bicep stack."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [security, threat-model, stride, red-team]
    related_skills: [sec-static-scan, sec-config-review]
    memory_profiles: [security]
---

# sec-threat-model

## Title
 sec-threat-model — Threat Model Authoring

## Description
Produce or refresh a STRIDE-style threat model for the SWA + VM API + Bicep stack, persisted under `<workspace>/security/threat-model.md`. Bind findings to the `security` memory profile and update a changelog on refresh. When queried, summarize the top 5 threats by severity with affected components and mitigation status.

## Trigger Conditions
- User invokes `/sec threat-model`
- User asks to review security posture or create a threat model

## Inputs
- Workspace path (resolved via `workspaces.yaml`)
- Existing `security/threat-model.md` (if present)

## Outputs
- `<workspace>/security/threat-model.md`
- Memory profile updates

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the red-team bundle.
