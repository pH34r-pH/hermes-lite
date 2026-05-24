---
name: sec-static-scan
description: "Run ripgrep secret scanning, dependency CVE audit, and Bicep linter."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [security, static-scan, secrets, cve, bicep, red-team]
    related_skills: [sec-threat-model, sec-config-review]
    memory_profiles: [security]
---

# sec-static-scan

## Title
 sec-static-scan — Static Security Scanning

## Description
Run ripgrep-based secret scanning with configurable ignore-lists (`.secretscanignore`) and comment annotations. Run dependency CVE scanning via `pip-audit`, `npm audit`, `cargo audit`, and `gh advisory` as applicable. Run a Bicep linter pass over `infra/` files. Return structured findings with file path, line number, rule name, and severity. On clean scan, update the security baseline in the memory profile.

## Trigger Conditions
- User invokes `/sec static-scan`
- User asks to scan for secrets, CVEs, or misconfigurations

## Inputs
- Workspace path
- Scan scope: secrets, dependencies, bicep, or all

## Outputs
- Structured findings list
- Updated security baseline (on clean scan)

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the red-team bundle.
