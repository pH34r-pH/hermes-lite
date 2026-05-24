# Tasks: `hermes-lite doctor` Command

**Input**: Design documents from `/specs/014-doctor-command/`

**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Tests are included as specified in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Module scaffold, output primitive reuse, upstream integration verification

- [x] T001 Create `hermes_cli/doctor_lite.py` with module docstring and `DoctorLite` class stub
- [x] T002 Verify `hermes_cli/doctor.py` exists; extract or document reuse of `check_ok`, `check_warn`, `check_fail`, `_section` primitives
- [x] T003 Verify `hermes_cli/cli_output.py` exists; document `print_success`, `print_warning`, `print_error` fallback primitives
- [x] T004 Verify `hermes_state.py` exists; document schema version integration point
- [x] T005 Verify `hermes_constants.py` exists; document `get_hermes_home()` path resolution
- [x] T006 Verify `hermes_cli/commands.py` exists; document `doctor` subcommand registration integration point
- [x] T007 Verify `gateway/platforms/discord/` exists; document `discord.py` import check integration point
- [x] T008 Verify `ui-tui/` exists; document TUI availability check integration point
- [x] T009 [P] Add `doctor` CLI subcommand registration stub in `hermes_cli/commands.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core check primitives and output framework that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T010 Implement output primitives in `hermes_cli/doctor_lite.py`
  - Reuse or reimplement `check_ok(text, detail)`, `check_warn(text, detail)`, `check_fail(text, detail)`, `_section(title)`
  - Match upstream visual style (✓ green, ⚠ yellow, ✗ red, bold section headers)
- [x] T011 Implement `OllamaProbe` in `hermes_cli/doctor_lite.py`
  - HTTP GET against `http://127.0.0.1:11434`
  - Run `ollama list` and verify configured default model is present
  - On failure: print remediation command (`sudo systemctl start ollama`)
- [x] T012 Implement `CredentialPresenceCheck` in `hermes_cli/doctor_lite.py`
  - Check `OPENAI_API_KEY`, `GITHUB_COPILOT_TOKEN` (or ACP auth state), `ANTHROPIC_API_KEY`
  - Absence is a warning, not a failure
  - Avoid live API calls to prevent rate-limit consumption
- [x] T013 Implement `StateDbSchemaCheck` in `hermes_cli/doctor_lite.py`
  - Read `state.db` `PRAGMA user_version` or verify expected table existence
  - Compare against expected hermes-lite schema version
  - Report mismatch as failure with migration hint
- [x] T014 Implement `DiskSpaceCheck` in `hermes_cli/doctor_lite.py`
  - `shutil.disk_usage` on `~/.hermes-lite/`
  - Warn when below 10 GB (configurable via `lite-config.yaml`)
- [x] T015 Implement `ThermalCheck` in `hermes_cli/doctor_lite.py`
  - Parse `tegrastats` output for CPU temp, GPU temp, `nvpmodel` mode, throttling flags
  - Warn on thermal alarm (CPU > 85 °C or GPU > 85 °C)
  - Skip gracefully on non-Jetson hosts
- [x] T016 Implement `WorkspaceHealthCheck` in `hermes_cli/doctor_lite.py`
  - Read `~/.hermes-lite/workspaces.yaml`
  - Verify each registered workspace path exists on disk
  - Verify git authentication via `ssh -T git@github.com` or `gh auth status`
- [x] T017 Implement `SkillsIndexCheck` in `hermes_cli/doctor_lite.py`
  - Use `ripgrep` (with `os.walk` fallback) to validate required skill bundles
  - Report missing bundles as failures
- [x] T018 Implement `TuiAvailabilityCheck` in `hermes_cli/doctor_lite.py`
  - Verify `ui-tui/` dependencies installed (package.json, node_modules)
  - Verify compiled bundle exists and entry point is executable
- [x] T019 Implement `GatewayBindingCheck` in `hermes_cli/doctor_lite.py`
  - Discord: verify `discord.py` importable and `DISCORD_BOT_TOKEN` present if enabled
  - Open WebUI: verify pipeline adapter importable and gateway config present if enabled
- [x] T020 Implement `DoctorLite.run()` orchestration in `hermes_cli/doctor_lite.py`
  - Execute all checks in order; track warnings and failures
  - Exit 0 if only warnings; exit non-zero if any failures
  - Support `--fix` flag for safe auto-remediation

**Checkpoint**: Foundation ready — all check primitives exist and can be invoked independently; user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Verify Offline-First Baseline (Priority: P1) 🎯 MVP

**Goal**: Doctor must not block usage when only local resources are available

**Independent Test**: Run `hermes-lite doctor` with no network and no `.env` keys; verify exit 0 with warnings

### Tests for User Story 1

- [x] T021 [P] [US1] Unit test: `OllamaProbe` returns OK when daemon is reachable in `tests/unit/test_doctor_lite.py`
- [x] T022 [P] [US1] Unit test: `CredentialPresenceCheck` warns but does not fail when no keys are set in `tests/unit/test_doctor_lite.py`
- [x] T023 [P] [US1] Unit test: `TuiAvailabilityCheck` returns OK when dependencies present in `tests/unit/test_doctor_lite.py`
- [x] T024 [P] [US1] Integration test: offline-only configuration exits 0 with warnings in `tests/integration/test_doctor_lite.py`

### Implementation for User Story 1

- [x] T025 [US1] Integrate `OllamaProbe` into `DoctorLite.run()` — first check, failure is fatal
- [x] T026 [US1] Integrate `CredentialPresenceCheck` into `DoctorLite.run()` — warning only
- [x] T027 [US1] Integrate `TuiAvailabilityCheck` into `DoctorLite.run()`
- [x] T028 [US1] Ensure no external network probes are made when offline
- [x] T029 [US1] Ensure execution completes in under 10 seconds

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Detect Local Resource Issues (Priority: P1)

**Goal**: Hardware health directly impacts model inference latency and agent responsiveness

**Independent Test**: Simulate low disk space and high temperature; verify doctor reports accurately

### Tests for User Story 2

- [x] T030 [P] [US2] Unit test: `DiskSpaceCheck` warns when below 10 GB in `tests/unit/test_doctor_lite.py`
- [x] T031 [P] [US2] Unit test: `ThermalCheck` warns when CPU > 85 °C in `tests/unit/test_doctor_lite.py`
- [x] T032 [P] [US2] Unit test: `StateDbSchemaCheck` fails on schema mismatch in `tests/unit/test_doctor_lite.py`
- [x] T033 [P] [US2] Unit test: `ThermalCheck` skips gracefully on non-Jetson in `tests/unit/test_doctor_lite.py`
- [x] T034 [P] [US2] Integration test: synthetic low-disk and high-temp conditions reported correctly in `tests/integration/test_doctor_lite.py`

### Implementation for User Story 2

- [x] T035 [US2] Integrate `DiskSpaceCheck` into `DoctorLite.run()`
  - Print exact GB remaining; suggest cleanup steps on warning
- [x] T036 [US2] Integrate `ThermalCheck` into `DoctorLite.run()`
  - Report `nvpmodel` mode; recommend 25 W mode on thermal alarm
- [x] T037 [US2] Integrate `StateDbSchemaCheck` into `DoctorLite.run()`
  - Print schema version on success; print migration command on mismatch
- [x] T038 [US2] Add container detection (`.dockerenv`, cgroup `container`) to skip systemd/thermal checks

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validate Gateway and Workspace Bindings (Priority: P2)

**Goal**: Reduce time-to-first-prompt by verifying gateway and workspace setup

**Independent Test**: Configure Discord and Open WebUI tokens, register workspaces, run doctor

### Tests for User Story 3

- [x] T039 [P] [US3] Unit test: `GatewayBindingCheck` returns OK when Discord token present and enabled in `tests/unit/test_doctor_lite.py`
- [x] T040 [P] [US3] Unit test: `GatewayBindingCheck` returns OK when Open WebUI adapter importable and enabled in `tests/unit/test_doctor_lite.py`
- [x] T041 [P] [US3] Unit test: `WorkspaceHealthCheck` fails when registered workspace path missing in `tests/unit/test_doctor_lite.py`
- [x] T042 [P] [US3] Unit test: `WorkspaceHealthCheck` warns when SSH agent has no identities in `tests/unit/test_doctor_lite.py`
- [x] T043 [P] [US3] Integration test: missing workspace reported with clone suggestion in `tests/integration/test_doctor_lite.py`

### Implementation for User Story 3

- [x] T044 [US3] Integrate `GatewayBindingCheck` into `DoctorLite.run()`
  - Only run checks for gateways enabled in `lite-config.yaml`
- [x] T045 [US3] Integrate `WorkspaceHealthCheck` into `DoctorLite.run()`
  - Print `ℹ No workspaces registered` as informational (not failure) when registry is empty
- [x] T046 [US3] Ensure Discord check does not crash when `discord.py` is not installed
- [x] T047 [US3] Ensure Open WebUI check verifies pipeline adapter importability, not just config presence

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Skills Index and state.db Validation (Priority: P2)

**Goal**: After upgrades, verify skills index and session database compatibility

**Independent Test**: Corrupt skills index, run doctor, verify failure is reported

### Tests for User Story 4

- [x] T048 [P] [US4] Unit test: `SkillsIndexCheck` returns OK when all required bundles present in `tests/unit/test_doctor_lite.py`
- [x] T049 [P] [US4] Unit test: `SkillsIndexCheck` fails when required bundle missing in `tests/unit/test_doctor_lite.py`
- [x] T050 [P] [US4] Unit test: `SkillsIndexCheck` falls back to `os.walk` when `ripgrep` missing in `tests/unit/test_doctor_lite.py`
- [x] T051 [P] [US4] Unit test: `--fix` migrates synthetic old-schema `state.db` in `tests/unit/test_doctor_lite.py`
- [x] T052 [P] [US4] Integration test: missing skill bundle causes non-zero exit in `tests/integration/test_doctor_lite.py`

### Implementation for User Story 4

- [x] T053 [US4] Integrate `SkillsIndexCheck` into `DoctorLite.run()`
  - Scan `skills/` and `optional-skills/` for bundles required by active `lite-config.yaml` profile
  - Missing bundles cause non-zero exit
- [x] T054 [US4] Implement `--fix` flag in `hermes_cli/doctor_lite.py`
  - Attempt `state.db` minor migration automatically
  - Attempt `ollama pull` for missing default model
  - Report success or failure per fix attempt
- [x] T055 [US4] Ensure `ripgrep` missing degradation prints warning suggesting `sudo apt install ripgrep`
- [x] T056 [US4] Ensure TUI check suggests `npm run build` in `ui-tui/` when compiled bundle is out of date

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Edge cases, performance, safety, and final integration

- [x] T057 Verify malformed `lite-config.yaml` is parsed defensively; parse error reported, dependent checks skipped
- [x] T058 Verify missing Ollama daemon is reported as failure with clear remediation command
- [x] T059 Verify empty workspace registry prints informational note, not failure
- [x] T060 Verify non-Jetson host skips thermal checks gracefully
- [ ] T061 Verify container detection skips systemd and thermal checks
- [ ] T062 Verify no removed provider modules are imported (verified by import-trap test)
- [ ] T063 Verify `--fix` does not modify user code or config files
- [ ] T064 Verify `--fix` `state.db` migration is idempotent and safe
- [ ] T065 Verify command completes in under 10 seconds on Jetson Orin Nano with no network
- [ ] T066 Verify exit code is 0 when only warnings present; non-zero when any check fails
- [ ] T067 Verify output style matches upstream `check_ok` / `check_warn` / `check_fail` / `_section` primitives
- [ ] T068 [P] Run retained unit-test suite and confirm zero regressions in CLI commands or doctor functionality
- [ ] T069 Update `REDESIGN.md` §5.8 references to reflect completed implementation
- [ ] T070 Update `specs/014-doctor-command/` status to Complete

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) — Builds on US1 baseline but tests standalone resources
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) — Builds on US1+US2 but tests gateway/workspace bindings independently
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) — Builds on US1+US2+US3 but tests skills/state independently

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Check primitives before integration into `DoctorLite.run()`
- Core implementation before `--fix` handling
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- US1 (offline baseline) and US4 (skills/state) are orthogonal and can proceed in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Ollama + credentials + TUI offline check)
4. **STOP and VALIDATE**: Run `hermes-lite doctor` with no network and no keys; verify exit 0 with warnings
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Polish and final validation
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (offline baseline) + User Story 2 (local resources)
   - Developer B: User Story 3 (gateway + workspace bindings)
   - Developer C: User Story 4 (skills index + state.db) + `--fix` support
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- The command MUST NOT import or check any removed providers, gateways, or dependencies
- `--fix` MUST be limited to safe, idempotent operations; it MUST NOT modify user code
- Credential checks MUST be presence-only; avoid live API calls
- Thermal checks MUST skip gracefully on non-Jetson hosts
- `ripgrep` missing MUST degrade to `os.walk` with a warning
