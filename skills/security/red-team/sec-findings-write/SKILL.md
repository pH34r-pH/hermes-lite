---
name: sec-findings-write
description: "Write structured findings report and emit spec-seed.json for spec-kit consumption."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [security, findings, report, spec-seed, red-team]
    related_skills: [sec-fuzz, sec-rotate-credentials]
    memory_profiles: [security]
---

# sec-findings-write

## Title
 sec-findings-write — Security Findings Reporting

## Description
Write a structured findings report under `<workspace>/security/findings/<date>-<topic>.md` with severity, reproduction steps, and recommended fix. Emit a `spec-seed.json` to `~/repos/knowledge/seeds/<finding-id>.json` so the spec-kit can implement the fix through the tracked PR loop. Cross-repo fixes become two coordinated specs with linked IDs.

## Trigger Conditions
- User invokes `/sec findings-write`
- User asks to document or report security findings

## Inputs
- Findings from prior scan or probe skills
- Target workspace

## Outputs
- `<workspace>/security/findings/<date>-<topic>.md`
- `~/repos/knowledge/seeds/<finding-id>.json`

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the red-team bundle.
