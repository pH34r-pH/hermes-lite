---
name: red-team
description: "Root bundle descriptor for security red-team operations. Exposes /sec slash command with 9 sequential skills."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [red-team, bundle, security, pentest, self-pentest]
    related_skills: [blue-team]
    memory_profiles: [security, web, api, infra]
---

# Red-Team Skill Bundle

The `red-team` bundle implements a complete self-pentest discipline against the agent's own deployed surface (SWA + VM API + Bicep stack). It exposes the `/sec` slash command and provides 9 sequential skills, each sized for a 3B model context.

## Sequential Pipeline

1. **sec-threat-model** — Produce or refresh a STRIDE-style threat model under `<workspace>/security/threat-model.md`
2. **sec-static-scan** — Run ripgrep secret scanning, dependency CVE audit (`pip-audit`, `npm audit`, `cargo audit`, `gh advisory`), and Bicep linter
3. **sec-config-review** — Review `staticwebapp.config.json`, CORS rules, CSP headers, reverse-proxy config, systemd hardening, Tailscale ACLs, and Key Vault access policies against baseline
4. **sec-auth-probe** — Active auth checks: missing-auth, expired-token replay, role escalation, CORS pre-flight abuse
5. **sec-web-probe** — Active web checks: directory listing, broken links, mixed content, open redirect, cookie attributes via `plugins/browser/`
6. **sec-rate-limit-probe** — Controlled burst testing against allowlisted endpoints with strict iteration budget
7. **sec-fuzz** — Schema-driven fuzzing of API request bodies with fixed iteration budget and recorded corpus
8. **sec-findings-write** — Write structured findings report and emit `spec-seed.json` to spec-kit
9. **sec-rotate-credentials** — Rotate API keys, SSH keys, Tailscale auth keys; update Key Vault and systemd env file; never log secrets

## Approval Gates

- **active-probe**: Every active probe (skills 4-7) requires workspace `approval_mode` of at least `confirm`
- **credential-rotation**: `sec-rotate-credentials` always runs in `approval_mode: confirm` regardless of workspace default

## Key Entities

- **ThreatModel**: STRIDE-style markdown document mapping threats to SWA, VM API, and Bicep components
- **SecurityScope**: `~/.hermes-lite/security-scope.yaml` declaring owned hostnames for probe targets
- **FindingsReport**: Structured markdown under `<workspace>/security/findings/<date>-<topic>.md`
- **ProbeBudget**: Per-probe iteration and rate limit enforced at the agent layer
- **SpecSeed**: JSON envelope produced by `sec-findings-write` and consumed by spec-kit

## Memory Profile Bindings

- `security` — write-only for `/sec` kit; contains threat models, baselines, findings history, rotation events
- `web`, `api`, `infra` — read-only for context during scans and probes

## Safety Rules

- Active probes target **only** hostnames declared in `~/.hermes-lite/security-scope.yaml`; egress filter blocks all other hosts
- Active probes are rate-limited at the agent layer in addition to target-enforced limits
- Findings are never auto-fixed; they always feed the spec-kit through `spec-seed.json`
- No secrets appear in agent logs, gateway messages, or `state.db`
- All `/sec` skills emit structured events to `logs/security.jsonl` with mode 0600 rotation

## Notes

This is a skeleton bundle. Full skill logic implementation is pending per `specs/009-security-redteam-bundle/`.
