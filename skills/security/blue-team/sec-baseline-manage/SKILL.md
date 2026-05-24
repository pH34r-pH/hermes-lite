---
name: sec-baseline-manage
description: "Store, compare, and update security baselines for config files and scan results."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [security, baseline, blue-team, config]
    related_skills: [sec-config-review, sec-audit-readiness]
    memory_profiles: [security]
---

# sec-baseline-manage

## Title
 sec-baseline-manage — Security Baseline Management

## Description
Store, compare, and update security baselines for config files and scan results using `BaselineStore`. Compute delta between stored baseline and current scan or config state. Emit delta report with previous state and recommendation.

## Trigger Conditions
- User invokes `/sec baseline`
- User asks to update or compare security baselines

## Inputs
- Current config files or scan results
- Stored baseline from `~/.hermes-lite/baselines/`

## Outputs
- Delta report
- Updated baseline (on user approval)

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the blue-team bundle.
