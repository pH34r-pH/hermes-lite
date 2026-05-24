# Implementation Plan: Security & Red-Team Ops Kit

**Branch**: `009-security-redteam-bundle` | **Date**: 2026-05-24 | **Spec**: `specs/009-security-redteam-bundle/spec.md`

**Input**: Feature specification from `/specs/009-security-redteam-bundle/spec.md`

## Summary

Ship a complete `skills/security/red-team/` bundle plus a `skills/security/blue-team/` subtree, exposed through a single `/sec` slash command. The bundle implements 9 sequential red-team skills (`sec-threat-model`, `sec-static-scan`, `sec-config-review`, `sec-auth-probe`, `sec-web-probe`, `sec-rate-limit-probe`, `sec-fuzz`, `sec-findings-write`, `sec-rotate-credentials`) and 3 blue-team skills (`sec-baseline-manage`, `sec-log-review`, `sec-audit-readiness`), each sized for a 3B model context. All active probes target only the agent's own deployed surface (SWA + VM API + Bicep stack) as declared in `~/.hermes-lite/security-scope.yaml`. Active probes require `approval_mode: confirm` and are rate-limited at the agent layer. Findings feed the spec-kit via `spec-seed.json`; they are never auto-fixed. The `security` memory profile is write-only to the `/sec` kit and read-only to all other kits. Egress filtering is enforced by `agent/tool_guardrails.py` and systemd-level IP filtering, neither mutable by the `/sec` kit.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: `ripgrep` (system), `pip-audit` / `npm` / `cargo` (system, for dependency CVE scanning), `jsonschema` (Bicep / config validation), `requests` (active probes), existing `agent/tool_guardrails.py`, existing `agent/file_safety.py`, existing `plugins/browser/` (for `sec-web-probe`), existing `agent/redact.py`, existing `plugins/local_repo_workspace/` (spec 010), existing spec-kit bundle (spec 007)

**Storage**: `~/.hermes-lite/security-scope.yaml` (owned hostnames), `<workspace>/security/threat-model.md` (STRIDE model), `<workspace>/security/findings/<date>-<topic>.md` (findings reports), `~/repos/knowledge/seeds/<finding>.json` (spec-seed output), `~/.hermes-lite/logs/security.jsonl` (structured security events, mode 0600), `~/.hermes-lite/baselines/` (blue-team config baselines), `state.db` (conversation mapping and security memory profile)

**Testing**: pytest, plus integration tests requiring a staging deployment reachable from the Jetson and an Azure Key Vault sandbox

**Target Platform**: Linux (Jetson Orin Nano) for agent; Azure cloud / VM for target surface; browser-based SWA for web probes

**Project Type**: Two coordinated skill bundles with Python support modules, YAML configuration, and agent-layer guardrail integration

**Performance Goals**: `sec-threat-model` completes within 60 seconds on Jetson 25 W mode; `sec-static-scan` completes within 120 seconds for a medium repo; `sec-auth-probe` and `sec-web-probe` never exceed their rate budget; full kit pass completes end-to-end in under 10 minutes for a single target

**Constraints**: Active probes (skills 4-7) require `approval_mode: confirm`; `sec-rotate-credentials` is always confirmation-mode regardless of workspace default; egress filter blocks all non-owned hosts; no secrets logged in agent logs; security memory profile write-only for `/sec` kit; findings never auto-fixed;fuzz iteration budget is strict and stops exactly at limit

**Scale/Scope**: Two bundles (~12 SKILL.md files total), Python support libraries for scanning, probing, and egress filtering (~800-1000 LOC), YAML schema for `security-scope.yaml`, JSON schema for `spec-seed.json` emission, integration with agent tool guardrails and memory profile subsystem

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Security-First Development**: Active probes require explicit confirmation; credential rotation never logs secrets; egress filter blocks non-owned hosts; findings feed spec-kit rather than auto-fix.
- **Defense in Depth**: Egress filter enforced at both systemd level and `agent/tool_guardrails.py`; rate limits applied at agent layer in addition to target limits; security memory profile is write-isolated.
- **Secure Defaults**: `sec-rotate-credentials` always runs in confirmation mode; empty or missing `security-scope.yaml` blocks all active probes; empty user allowlist defaults to deny-all.
- **Dependency Management**: `ripgrep`, `pip-audit`, `npm`, `cargo`, and `az` are system dependencies; no heavy security SDK packages added to the Python environment.

**Result**: PASS — design aligns with all constitution principles.

## Project Structure

### Documentation (this feature)

```text
specs/009-security-redteam-bundle/
├── plan.md              # This file
├── spec.md              # Feature specification
└── tasks.md             # Concrete task list
```

### Source Code (repository root)

```text
skills/security/red-team/
├── SKILL.md                         # Root bundle descriptor
├── sec-threat-model/SKILL.md        # Skill 1 — STRIDE threat model
├── sec-static-scan/SKILL.md         # Skill 2 — secret + CVE + Bicep scan
├── sec-config-review/SKILL.md       # Skill 3 — config baseline delta
├── sec-auth-probe/SKILL.md          # Skill 4 — active auth checks
├── sec-web-probe/SKILL.md           # Skill 5 — active web checks
├── sec-rate-limit-probe/SKILL.md    # Skill 6 — controlled burst testing
├── sec-fuzz/SKILL.md                # Skill 7 — schema-driven fuzzing
├── sec-findings-write/SKILL.md      # Skill 8 — structured findings + spec-seed
├── sec-rotate-credentials/SKILL.md  # Skill 9 — key rotation (always confirm)
├── manifest.yaml                    # Bundle manifest registering `/sec` slash command
└── lib/
    ├── __init__.py
    ├── egress_filter.py             # Hostname allowlist enforcer + request interceptor
    ├── probe_budget.py              # Per-probe iteration / rate limit tracker
    ├── scan_runner.py               # ripgrep, pip-audit, npm audit, cargo audit orchestrator
    ├── threat_model_writer.py       # STRIDE markdown generator + changelog updater
    ├── findings_reporter.py         # Markdown findings formatter + spec-seed.json emitter
    └── fuzz_engine.py               # Schema-driven fuzz corpus generator + request recorder

skills/security/blue-team/
├── SKILL.md                         # Root bundle descriptor
├── sec-baseline-manage/SKILL.md     # Baseline store / compare / update
├── sec-log-review/SKILL.md          # Bounded journalctl parsing + signature matching
├── sec-audit-readiness/SKILL.md     # Artifact existence + freshness checks
├── manifest.yaml                    # Bundle manifest (no slash command; loaded by `/sec`)
└── lib/
    ├── __init__.py
    ├── baseline_store.py            # Baseline JSON read/write under ~/.hermes-lite/baselines/
    ├── audit_checker.py             # Artifact freshness checker
    └── log_parser.py                # Bounded journalctl wrapper + signature patterns

agent/
└── tool_guardrails.py               # UPDATE — add egress filter hook + probe rate limiter

agent/
└── memory_manager.py                # UPDATE — enforce security memory profile write isolation

~/.hermes-lite/security-scope.yaml    # Owned hostname / endpoint declaration schema
~/.hermes-lite/logs/security.jsonl    # Structured security event log (mode 0600)
```

**Structure Decision**: Two separate bundles within `skills/security/` because red-team and blue-team have fundamentally different authority models: red-team performs active probes requiring strict approval/egress constraints, while blue-team performs passive defense and audit checks. A single monolithic bundle would blur these authority boundaries. The shared `security` memory profile and `/sec` slash command unify them at the user interface layer.

## Complexity Tracking

> The feature introduces two bundles plus agent-layer guardrail changes. This is justified because:
> - Active red-team probes require agent-layer egress filtering and rate limiting that passive blue-team skills do not.
> - Credential rotation and active probing carry distinct blast-radius profiles that must be isolated in approval logic.
> - Separating red-team and blue-team skills lets the blue-team baseline manager read the `security` memory profile without also loading active probe tools into the model context.
>
> | Violation | Why Needed | Simpler Alternative Rejected Because |
> |-----------|------------|-------------------------------------|
> | Two bundles instead of one | Different authority models and blast-radius constraints; agent-layer guardrail integration only needed for red-team | Single bundle would load active probe tools during passive audit tasks, violating least-privilege and tool-surface slimming (spec 003) |
> | Agent-level guardrail changes (egress + rate limiter) | Must block probes at the agent boundary before they touch the network; skills alone cannot enforce this | Skill-level refusal is too late — a compromised or hallucinated skill could bypass it |
