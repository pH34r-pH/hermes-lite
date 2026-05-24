---
name: sec-rate-limit-probe
description: "Controlled burst testing against allowlisted endpoints with strict iteration budget."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [security, rate-limit, probe, red-team, active-probe]
    related_skills: [sec-auth-probe, sec-web-probe]
    memory_profiles: [security, api]
---

# sec-rate-limit-probe

## Title
 sec-rate-limit-probe — Rate Limit Probe

## Description
Perform controlled burst testing against allowlisted endpoints with a strict iteration budget enforced by `ProbeBudget`. The agent-layer rate limiter caps request rate and pauses on HTTP 403/429 responses. Never exceeds the configured budget.

## Trigger Conditions
- User invokes `/sec rate-limit-probe`
- User asks to test API rate limiting

## Inputs
- Target endpoints from `security-scope.yaml`
- Burst configuration (requests, concurrency, duration)
- Probe budget

## Outputs
- Rate limit test results
- Budget state log

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the red-team bundle.
