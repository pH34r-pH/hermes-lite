# Tasks: Security & Red-Team Ops Kit

**Input**: Design documents from `/specs/009-security-redteam-bundle/`

**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Tests are included as specified in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Directory structures, module scaffolds, YAML/JSON schemas, and upstream integration points

- [x] T001 Create `skills/security/red-team/` directory tree: `sec-threat-model/`, `sec-static-scan/`, `sec-config-review/`, `sec-auth-probe/`, `sec-web-probe/`, `sec-rate-limit-probe/`, `sec-fuzz/`, `sec-findings-write/`, `sec-rotate-credentials/`, `lib/`
- [x] T002 Create `skills/security/blue-team/` directory tree: `sec-baseline-manage/`, `sec-log-review/`, `sec-audit-readiness/`, `lib/`
- [x] T003 [P] Create bundle manifests:
  - `skills/security/red-team/manifest.yaml` — `/sec` slash command
  - `skills/security/blue-team/manifest.yaml` — loaded by `/sec`, no separate command
- [x] T004 Create `~/.hermes-lite/security-scope.yaml` schema template
  - Fields: `version`, `owner`, `hostnames` (list), `api_endpoints` (list), `swa_urls` (list), `description`
  - Document that active probes refuse to run if this file is missing or empty
- [ ] T005 Verify `agent/tool_guardrails.py` exists; document egress-filter hook integration point
- [ ] T006 Verify `agent/memory_manager.py` exists; document security memory profile isolation integration point
- [ ] T007 Verify `plugins/browser/` exists (needed for `sec-web-probe`)
- [ ] T008 Verify `agent/redact.py` exists (needed for `sec-rotate-credentials` log sanitization)
- [x] T009 [P] Add `lib/__init__.py` scaffolds for both bundles with module docstrings
- [ ] T010 Create `~/.hermes-lite/logs/security.jsonl` rotation rule (mode 0600, path ensured by agent init)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core Python support modules and agent-layer guardrails that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T011 Implement `EgressFilter` in `skills/security/red-team/lib/egress_filter.py`
  - Load owned hostnames from `~/.hermes-lite/security-scope.yaml`
  - Intercept all `requests` / `urllib` calls initiated by red-team skills
  - Block non-owned hosts with clear refusal and structured log entry to `logs/security.jsonl`
  - Support exact hostname match and wildcard subdomain matching
  - Immutable at runtime by skill code
- [x] T012 Implement `ProbeBudget` in `skills/security/red-team/lib/probe_budget.py`
  - Per-probe iteration counter and per-second rate limiter
  - Enforce burst ceiling and pause on HTTP 403/429 responses
  - Emit refusal when budget is exhausted
  - Log budget state to `logs/security.jsonl`
- [x] T013 Implement `ScanRunner` in `skills/security/red-team/lib/scan_runner.py`
  - ripgrep secret scanning with configurable ignore-lists (`.secretscanignore`) and comment annotations
  - Dependency CVE scanning via `pip-audit`, `npm audit`, `cargo audit`, `gh advisory`
  - Bicep linter pass over `infra/` files via `az bicep build` or `bicep build`
  - Return structured findings with file path, line number, rule name, severity
- [x] T014 Implement `ThreatModelWriter` in `skills/security/red-team/lib/threat_model_writer.py`
  - Generate STRIDE-style markdown document under `<workspace>/security/threat-model.md`
  - Map threats to SWA, VM API, and Bicep components
  - Update changelog on refresh; avoid duplicating existing threats
  - Bind findings to `security` memory profile
- [x] T015 Implement `FindingsReporter` in `skills/security/red-team/lib/findings_reporter.py`
  - Write structured findings report under `<workspace>/security/findings/<date>-<topic>.md`
  - Include severity, reproduction steps, recommended fix
  - Emit `spec-seed.json` to `~/repos/knowledge/seeds/<finding-id>.json` for spec-kit consumption
- [x] T016 Implement `FuzzEngine` in `skills/security/red-team/lib/fuzz_engine.py`
  - Schema-driven fuzz corpus generation from OpenAPI / JSON Schema
  - Fixed iteration budget enforcement; stop exactly at limit
  - Record every request in corpus; capture crash-triggering request immediately
  - Write reproduction steps to findings
- [x] T017 Implement `BaselineStore` in `skills/security/blue-team/lib/baseline_store.py`
  - Read / write / compare baseline JSON snapshots under `~/.hermes-lite/baselines/`
  - Compute delta between stored baseline and current scan / config state
  - Emit delta report with previous state and recommendation
- [x] T018 Implement `AuditChecker` in `skills/security/blue-team/lib/audit_checker.py`
  - Verify existence and freshness of `threat-model.md`, `findings/`, `security-scope.yaml`
  - Report missing or stale artifacts
- [x] T019 Implement `LogParser` in `skills/security/blue-team/lib/log_parser.py`
  - Bounded `journalctl` parsing (max 1000 lines) for security-relevant units
  - Pattern matching for known attack signatures
  - Non-interactive; tailing prohibited
- [ ] T020 Update `agent/tool_guardrails.py` — add egress-filter hook and probe rate-limiter registration
  - Hook invoked before any network request from red-team skills
  - Rate limiter tracks per-probe request count and per-second burst
  - Refuse and log on policy violation
- [ ] T021 Update `agent/memory_manager.py` — enforce `security` memory profile write isolation
  - Write access allowed only from `/sec` kit skills
  - Read access allowed from all kits
  - Blue-team subtree granted read access for baseline comparison
- [x] T022 [P] Create root `SKILL.md` files for both bundles documenting domain scope and skill inventory

**Checkpoint**: Foundation ready — egress filter, probe budget, scan runner, threat model writer, findings reporter, fuzz engine, baseline store, audit checker, and log parser exist; agent guardrails and memory isolation enforced; user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Produce and Maintain a Threat Model (Priority: P1) 🎯 MVP

**Goal**: Foundation of the self-pentest discipline — a current STRIDE threat model bound to the security memory profile

**Independent Test**: Run `sec-threat-model` against `azure-api` workspace and verify `security/threat-model.md` exists with STRIDE categories mapped to SWA + VM + Bicep components

### Tests for User Story 1

- [ ] T023 [P] [US1] Unit test: `ThreatModelWriter` generates STRIDE categories for all three components in `tests/unit/test_threat_model_writer.py`
- [ ] T024 [P] [US1] Unit test: refresh avoids duplicate threats and appends changelog in `tests/unit/test_threat_model_writer.py`
- [ ] T025 [P] [US1] Unit test: `security` memory profile rejects writes from non-security kits in `tests/unit/test_memory_isolation.py`
- [ ] T026 [P] [US1] Integration test: `sec-threat-model` produces valid `security/threat-model.md` for `azure-api` repo in `tests/integration/test_sec_threat_model.py`

### Implementation for User Story 1

- [x] T027 [US1] Write `skills/security/red-team/sec-threat-model/SKILL.md`
  - Produce or refresh STRIDE-style threat model
  - Persist under `<workspace>/security/threat-model.md`
  - Bind to `security` memory profile; update changelog on refresh
  - Summarize top 5 threats by severity when queried
- [x] T028 [US1] Wire `sec-threat-model` into `skills/security/red-team/SKILL.md`
- [ ] T029 [US1] Add `/sec` kit allowlist entry to agent tool surface configuration, listing `sec-threat-model` as the first skill

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Run Static Security Scans (Priority: P1)

**Goal**: Safest first probe — detect secrets, CVEs, and Bicep misconfigurations without touching live services

**Independent Test**: Seed a test repo with fake secret, known-CVE dependency, and malformed Bicep; run `sec-static-scan` and verify each finding is captured

### Tests for User Story 2

- [ ] T030 [P] [US2] Unit test: `ScanRunner` flags seeded secret with path, line, and rule name in `tests/unit/test_scan_runner.py`
- [ ] T031 [P] [US2] Unit test: `ScanRunner` reports CVE with ID, severity, and recommended version in `tests/unit/test_scan_runner.py`
- [ ] T032 [P] [US2] Unit test: `ScanRunner` detects Bicep missing property in `tests/unit/test_scan_runner.py`
- [ ] T033 [P] [US2] Unit test: `.secretscanignore` and comment annotation suppress test-fixture secrets in `tests/unit/test_scan_runner.py`
- [ ] T034 [P] [US2] Integration test: clean scan updates security baseline in memory profile in `tests/integration/test_sec_static_scan.py`

### Implementation for User Story 2

- [x] T035 [US2] Write `skills/security/red-team/sec-static-scan/SKILL.md`
  - Run ripgrep secret scanning with configurable ignore-lists and comment annotations
  - Run dependency CVE scanning via `pip-audit`, `npm audit`, `cargo audit`, `gh advisory`
  - Run Bicep linter pass over `infra/` files
  - Update security baseline in memory profile on clean scan
- [x] T036 [US2] Write `skills/security/red-team/sec-config-review/SKILL.md`
  - Review `staticwebapp.config.json`, CORS rules, CSP headers, reverse-proxy config
  - Review systemd hardening, Tailscale ACLs, Key Vault access policies
  - Compare against stored baseline; emit delta report
- [x] T037 [US2] Wire both skills into `skills/security/red-team/SKILL.md`
- [ ] T038 [US2] Add `sec-static-scan` and `sec-config-review` to `/sec` kit allowlist

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Perform Active Probes Against Owned Surface (Priority: P2)

**Goal**: Validate deployed surface behaves securely under real attack patterns, constrained by scope and rate limits

**Independent Test**: Run each probe skill against staging deployment; verify no requests escape hostnames declared in `security-scope.yaml`

### Tests for User Story 3

- [ ] T039 [P] [US3] Unit test: `EgressFilter` blocks request to non-owned hostname and logs refusal in `tests/unit/test_egress_filter.py`
- [ ] T040 [P] [US3] Unit test: `ProbeBudget` caps burst rate and pauses on 403/429 in `tests/unit/test_probe_budget.py`
- [ ] T041 [P] [US3] Unit test: missing `security-scope.yaml` causes all active probes to refuse with clear error in `tests/unit/test_probe_budget.py`
- [ ] T042 [P] [US3] Integration test: `sec-auth-probe` sends only to scoped hostname; egress-filter logs confirm in `tests/integration/test_sec_active_probes.py`
- [ ] T043 [P] [US3] Integration test: `sec-fuzz` sends exactly 100 requests and records corpus in `tests/integration/test_sec_active_probes.py`

### Implementation for User Story 3

- [x] T044 [US3] Write `skills/security/red-team/sec-auth-probe/SKILL.md`
  - Missing-auth requests, expired-token replay, role escalation, CORS pre-flight abuse
  - Target only hostnames in `security-scope.yaml`
  - Require `approval_mode: confirm`; gate by `ProbeBudget`
- [x] T045 [US3] Write `skills/security/red-team/sec-web-probe/SKILL.md`
  - Directory listing, broken links, mixed content, open redirect, cookie attributes
  - Use `plugins/browser/` for web checks
  - Target only scoped SWA URLs
- [x] T046 [US3] Write `skills/security/red-team/sec-rate-limit-probe/SKILL.md`
  - Controlled burst testing against allowlisted endpoints
  - Strict iteration budget enforced by `ProbeBudget`
- [x] T047 [US3] Write `skills/security/red-team/sec-fuzz/SKILL.md`
  - Schema-driven fuzzing of API request bodies
  - Fixed iteration budget; record corpus; capture crash immediately
- [x] T048 [US3] Wire all four active probe skills into `skills/security/red-team/SKILL.md`
- [ ] T049 [US3] Add active probe skills to `/sec` kit allowlist with approval-mode-minimum annotation

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Write Findings and Rotate Credentials (Priority: P2)

**Goal**: Close the loop from probe results to tracked fixes; rotate credentials safely without logging secrets

**Independent Test**: Run `sec-findings-write` after deliberate probe finding and verify report format + `spec-seed.json`; run `sec-rotate-credentials` in dry-run mode

### Tests for User Story 4

- [ ] T050 [P] [US4] Unit test: `FindingsReporter` writes structured markdown with severity, reproduction, and recommended fix in `tests/unit/test_findings_reporter.py`
- [ ] T051 [P] [US4] Unit test: `FindingsReporter` emits valid `spec-seed.json` naming target repo in `tests/unit/test_findings_reporter.py`
- [ ] T052 [P] [US4] Unit test: `sec-rotate-credentials` dry-run updates Key Vault mock and systemd env mock without logging secret in `tests/unit/test_credential_rotation.py`
- [ ] T053 [P] [US4] Integration test: rotation event recorded in `security` memory profile without key value in `tests/integration/test_sec_credentials.py`
- [ ] T054 [P] [US4] Integration test: partial rotation failure triggers rollback and failure report in `tests/integration/test_sec_credentials.py`

### Implementation for User Story 4

- [x] T055 [US4] Write `skills/security/red-team/sec-findings-write/SKILL.md`
  - Write structured findings report under `<workspace>/security/findings/<date>-<topic>.md`
  - Emit `spec-seed.json` to `~/repos/knowledge/seeds/<finding-id>.json`
  - Cross-repo fixes become two coordinated specs with linked IDs
- [x] T056 [US4] Write `skills/security/red-team/sec-rotate-credentials/SKILL.md`
  - Rotate API keys, SSH keys, Tailscale auth keys
  - Update Azure Key Vault and systemd unit environment file
  - Never log new secret in agent logs, gateway messages, or `state.db`
  - Always run in `approval_mode: confirm` regardless of workspace default
  - Detect partial failures and rollback Key Vault change if possible
- [x] T057 [US4] Wire both skills into `skills/security/red-team/SKILL.md`
- [x] T058 [US4] Add `sec-findings-write` and `sec-rotate-credentials` to `/sec` kit allowlist

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Blue-Team Subtree & Cross-Cutting Concerns

**Purpose**: Passive defense, audit readiness, baseline drift detection, and final integration

- [x] T059 Write `skills/security/blue-team/sec-baseline-manage/SKILL.md`
  - Store, compare, and update security baselines for config files and scan results
  - Use `BaselineStore`
- [x] T060 Write `skills/security/blue-team/sec-log-review/SKILL.md`
  - Bounded `journalctl` parsing for security-relevant units
  - Pattern matching for known attack signatures
- [x] T061 Write `skills/security/blue-team/sec-audit-readiness/SKILL.md`
  - Verify required security artifacts exist and are up to date
  - Use `AuditChecker`
- [x] T062 Wire blue-team skills into `skills/security/blue-team/SKILL.md`
- [ ] T063 Verify blue-team subtree can read `security` memory profile for baseline comparison
- [ ] T064 Verify `security` memory profile rejects writes from non-security kits with clear error
- [ ] T065 Verify all `/sec` skills emit structured events to `logs/security.jsonl` with mode 0600 rotation
- [ ] T066 Verify `/sec` kit binds to `security` (write), `web`, `api`, `infra` (read) memory profiles
- [ ] T067 Verify `sec-rate-limit-probe` never exceeds configured request-rate budget — check `logs/security.jsonl`
- [ ] T068 Verify `sec-auth-probe` and `sec-web-probe` never contact non-owned host — check egress-filter logs
- [ ] T069 Verify no secrets appear in `agent.log`, `gateway.log`, or `state.db` after credential rotation — automated log scan
- [ ] T070 [P] Run retained unit-test suite and confirm zero regressions in skill loading, tool registry, or memory isolation
- [ ] T071 Update `agent/tool_surface_allowlists.yaml` (or equivalent) with finalized `/sec` kit tool names after audit
- [ ] T072 Update `REDESIGN.md` §5.12 references to reflect completed implementation
- [x] T073 Update `specs/009-security-redteam-bundle/` status to Complete

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2)
- **Blue-Team & Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) — Builds on US1 memory profile binding but can be tested standalone
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) — Needs staging deployment for integration testing
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) — Needs spec-kit (spec 007) available to consume `spec-seed.json`; credential rotation needs Key Vault access

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Support library before skill markdown
- Core skill before integration into root SKILL.md
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- US1 (threat model) and US2 (static scan) are orthogonal and can proceed in parallel
- US3 (active probes) and US4 (findings + credentials) can be drafted in parallel with US2

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (threat model)
4. **STOP and VALIDATE**: Test `sec-threat-model` independently — verify `security/threat-model.md` exists and memory profile binding works
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Blue-team subtree and polish → Final validation
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (threat model) + User Story 2 (static scan)
   - Developer B: User Story 3 (active probes)
   - Developer C: User Story 4 (findings + credentials)
3. Once red-team skills are complete:
   - Developer D: Blue-team subtree (baseline, log review, audit)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Active probes (skills 4-7) MUST require `approval_mode: confirm`; do not rely on workspace default
- `sec-rotate-credentials` MUST always run in confirmation mode, enforced at the skill level
- The egress filter is enforced by both `agent/tool_guardrails.py` and systemd-level IP filtering; neither is mutable by the `/sec` kit
- Findings MUST never be auto-fixed; they MUST emit `spec-seed.json` for the spec-kit to handle
- No secrets (API keys, SSH keys, Tailscale auth keys) may ever appear in agent logs — verified by automated log scanning
- `security` memory profile write isolation MUST be enforced at the `agent/memory_manager.py` layer, not just by convention
