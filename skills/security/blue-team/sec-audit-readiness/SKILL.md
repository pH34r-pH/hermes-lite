---
name: sec-audit-readiness
description: "Verify required security artifacts exist and are up to date."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [security, audit, blue-team, compliance]
    related_skills: [sec-baseline-manage, sec-log-review]
    memory_profiles: [security]
---

# sec-audit-readiness

## Title
 sec-audit-readiness — Audit Readiness Verification

## Description
Verify that required security artifacts (`threat-model.md`, `findings/`, `security-scope.yaml`) exist and are up to date. Report missing or stale artifacts using `AuditChecker`.

## Trigger Conditions
- User invokes `/sec audit`
- User asks to verify audit readiness or compliance

## Inputs
- Workspace path
- Required artifact list

## Outputs
- Audit readiness report: present / missing / stale artifacts

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the blue-team bundle.
