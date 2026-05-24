---
name: sec-auth-probe
description: "Active auth checks against deployed API: missing-auth, expired-token replay, role escalation, CORS pre-flight abuse."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [security, auth, probe, red-team, active-probe]
    related_skills: [sec-web-probe, sec-rate-limit-probe]
    memory_profiles: [security, api]
---

# sec-auth-probe

## Title
 sec-auth-probe — Authentication Probe

## Description
Perform active auth checks against the deployed API: missing-auth requests, expired-token replay, role-escalation attempts, and CORS pre-flight abuse. Target only hostnames in `security-scope.yaml`. Require `approval_mode: confirm`. Gate by `ProbeBudget` and agent-layer rate limits. Blocked requests log structured refusal events to `logs/security.jsonl`.

## Trigger Conditions
- User invokes `/sec auth-probe`
- User asks to test or probe API authentication

## Inputs
- Target API endpoints from `security-scope.yaml`
- Probe budget and rate limits

## Outputs
- Probe results: successful / blocked / unexpected responses
- Structured security events

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the red-team bundle.
