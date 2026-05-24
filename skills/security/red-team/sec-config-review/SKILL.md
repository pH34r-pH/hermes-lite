---
name: sec-config-review
description: "Review configs against baseline and emit delta report."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [security, config-review, baseline, delta, red-team]
    related_skills: [sec-static-scan, sec-baseline-manage]
    memory_profiles: [security, web, api, infra]
---

# sec-config-review

## Title
 sec-config-review — Configuration Review and Baseline Delta

## Description
Review `staticwebapp.config.json`, CORS rules, CSP headers, reverse-proxy config, systemd hardening, Tailscale ACLs, and Key Vault access policies against a stored baseline. Emit a delta report showing changed items, their previous baseline state, and recommendations.

## Trigger Conditions
- User invokes `/sec config-review`
- User asks to review security configurations

## Inputs
- Workspace path
- Stored baseline from `BaselineStore`

## Outputs
- Delta report: changed items, previous state, recommendations

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the red-team bundle.
