---
name: sec-web-probe
description: "Active web checks against deployed SWA: directory listing, broken links, mixed content, open redirect, cookie attributes."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [security, web, probe, red-team, active-probe]
    related_skills: [sec-auth-probe, sec-rate-limit-probe]
    memory_profiles: [security, web]
---

# sec-web-probe

## Title
 sec-web-probe — Web Application Probe

## Description
Perform active web checks against the deployed SWA: directory listing, broken links, mixed content, open redirect, and cookie attributes. Uses `plugins/browser/` for web checks. Targets only scoped SWA URLs from `security-scope.yaml`. Requires `approval_mode: confirm`. Gate by `ProbeBudget`.

## Trigger Conditions
- User invokes `/sec web-probe`
- User asks to test or probe the deployed web frontend

## Inputs
- Target SWA URLs from `security-scope.yaml`
- Probe budget and rate limits

## Outputs
- Probe results: findings with severity and reproduction steps
- Structured security events

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the red-team bundle.
