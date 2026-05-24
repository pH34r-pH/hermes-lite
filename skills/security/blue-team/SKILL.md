---
name: blue-team
description: "Root bundle descriptor for security blue-team operations. Loaded by /sec; no separate slash command."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [blue-team, bundle, security, baseline, audit]
    related_skills: [red-team]
    memory_profiles: [security]
---

# Blue-Team Skill Bundle

The `blue-team` bundle provides passive defense skills that complement the red-team probes. It is loaded by the `/sec` slash command and does not expose its own command.

## Skill Inventory

1. **sec-baseline-manage** — Store, compare, and update security baselines for config files and scan results using `BaselineStore`
2. **sec-log-review** — Bounded `journalctl` parsing for security-relevant units with pattern matching for known attack signatures using `LogParser`
3. **sec-audit-readiness** — Verify that required security artifacts (`threat-model.md`, `findings/`, `security-scope.yaml`) exist and are up to date using `AuditChecker`

## Key Entities

- **BlueTeamBaseline**: Stored snapshot of expected security configurations against which `sec-config-review` compares current state
- **AuditChecker**: Validates existence and freshness of required security artifacts

## Memory Profile Bindings

- `security` — read access for baseline comparison and audit-readiness (write is reserved for red-team kit)

## Notes

This is a skeleton bundle. Full skill logic implementation is pending per `specs/009-security-redteam-bundle/`.
