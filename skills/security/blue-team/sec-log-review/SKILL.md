---
name: sec-log-review
description: "Bounded journalctl parsing for security-relevant units with attack signature matching."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [security, logs, journalctl, blue-team]
    related_skills: [sec-baseline-manage, sec-audit-readiness]
    memory_profiles: [security, infra]
---

# sec-log-review

## Title
 sec-log-review — Security Log Review

## Description
Perform bounded `journalctl` parsing (max 1000 lines) for security-relevant units with pattern matching for known attack signatures. Non-interactive; tailing is prohibited.

## Trigger Conditions
- User invokes `/sec logs`
- User asks to review security logs

## Inputs
- Unit names (security-relevant)
- Line limit (default 100, max 1000)
- Attack signature patterns

## Outputs
- Matched log entries with signatures
- Summary of findings

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the blue-team bundle.
