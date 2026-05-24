# Tasks: Diagnostics Logging — Structured JSONL Streams

**Input**: Design documents from `/specs/012-diagnostics-logging/`

**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Tests are included as specified in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Module scaffold, directory creation, upstream integration verification

- [x] T001 Create `agent/diagnostics.py` with module docstring and singleton scaffold (`DiagnosticsLogger` class)
- [x] T002 Create `hermes_cli/logs_lite.py` with CLI argument parser stub (`--stream`, `--since`, `--tail`, `--grep`, `export --exclude`)
- [x] T003 Verify `hermes_logging.py` exists; document `RedactingFormatter` reuse integration point
- [x] T004 Verify `hermes_constants.py` exists; document `get_hermes_home()` path resolution for `~/.hermes-lite/logs/`
- [x] T005 Verify `cli.py` exists; document agent.jsonl event emission integration point
- [x] T006 Verify `run_agent.py` exists; document loop-end flush integration point
- [x] T007 [P] Add CLI subcommand registration stub in `hermes_cli/commands.py` for `logs`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T008 Implement `StableSchema` dataclass in `agent/diagnostics.py`
  - Fields: `ts` (ISO-8601 UTC), `session_id`, `kit`, `skill`, `provider`, `model`, `workspace`, `gateway`, `event`, `latency_ms`, `payload`
  - Default missing fields to `null` or `"__startup__"` for schema stability
- [x] T009 Implement `SecretRedactor` in `agent/diagnostics.py`
  - Reuse upstream `RedactingFormatter` patterns; replace API keys, tokens, passwords with `<redacted>`
  - Apply to `payload` object before JSON serialization
- [x] T010 Implement `LogStream` class in `agent/diagnostics.py`
  - Append-only JSONL writer per stream name
  - Daily rotation: new file at 00:00 UTC using filesystem mtime (not monotonic time)
  - 1 GB per-stream safety cap: stop appending and warn to `errors.log`
  - Graceful degradation on read-only / full filesystem: emit single warning, disable affected stream
- [x] T011 Implement `RetentionCleaner` in `agent/diagnostics.py`
  - Run at agent startup; delete stream files whose mtime is older than 90 days
  - Skip files with `.archive` suffix or inside `archive/` subdirectory
- [x] T012 Implement `ThermalSampler` in `agent/diagnostics.py`
  - Background thread polling `tegrastats` every 5 seconds when available
  - Parse CPU temp, GPU temp, `nvpmodel` power mode, throttling flags
  - Silently skip when `tegrastats` is unavailable (non-Jetson)
- [x] T013 Implement `DiagnosticsLogger` singleton wiring in `agent/diagnostics.py`
  - Expose `log(stream, event, payload, **context)` method
  - Initialize all seven streams: `agent`, `tools`, `providers`, `workspace`, `security`, `thermal`, `api`
  - Create `security` stream with filesystem mode `0600`
  - Create logs directory with mode `0700`

**Checkpoint**: Foundation ready — stable schema, redactor, log streams, rotation, retention, thermal sampler, and singleton exist; user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Emit and Query Agent Lifecycle Events (Priority: P1) 🎯 MVP

**Goal**: Agent stream is the backbone of the self-improvement loop

**Independent Test**: Start a session, verify `agent.jsonl` contains kit-load event, query via CLI helper

### Tests for User Story 1

- [x] T014 [P] [US1] Unit test: `StableSchema` outputs all top-level fields in `tests/unit/test_diagnostics_schema.py`
- [x] T015 [P] [US1] Unit test: `DiagnosticsLogger.log("agent", ...)` writes valid JSONL line in `tests/unit/test_diagnostics_agent.py`
- [x] T016 [P] [US1] Integration test: kit load event appears in `agent.jsonl` within 1 second in `tests/integration/test_diagnostics_agent.py`
- [x] T017 [P] [US1] Integration test: CLI helper `--stream agent --since today` returns only today's lines in `tests/integration/test_logs_cli.py`

### Implementation for User Story 1

- [x] T018 [US1] Emit `kit_load` event from `run_agent.py` or kit loader to `agent.jsonl` via `DiagnosticsLogger`
- [x] T019 [US1] Emit `kit_switch` event with old and new kit names in payload
- [x] T020 [US1] Emit `session_end` event with iteration count and elapsed time
- [x] T021 [US1] Implement CLI helper `--stream`, `--since`, `--tail` in `hermes_cli/logs_lite.py`
  - Parse date filters; tail last N lines; grep by simple key:value match
- [x] T022 [US1] Register `logs` CLI subcommand in `hermes_cli/commands.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Capture Tool Calls with Outcomes and Latency (Priority: P1)

**Goal**: Tool-call signal for refining tool surface and prompt templates

**Independent Test**: Invoke a tool and inspect `tools.jsonl` for the corresponding event line

### Tests for User Story 2

- [x] T023 [P] [US2] Unit test: `tools.jsonl` records `workspace.status` with `outcome: "success"` and `latency_ms > 0` in `tests/unit/test_diagnostics_tools.py`
- [x] T024 [P] [US2] Unit test: malformed JSON arguments record `outcome: "parse-fail"` with validation error in `tests/unit/test_diagnostics_tools.py`
- [x] T025 [P] [US2] Unit test: timeout records `outcome: "timeout"` in `tests/unit/test_diagnostics_tools.py`
- [x] T026 [P] [US2] Integration test: CLI `--stream tools --grep outcome:semantic-fail` returns matching lines in `tests/integration/test_logs_cli.py`

### Implementation for User Story 2

- [x] T027 [US2] Instrument `model_tools.py` `handle_function_call()` to emit `tool_call` events to `tools.jsonl`
  - Fields: `tool`, `arguments_hash`, `validation_result`, `latency_ms`, `outcome` enum
  - Outcome enum: `success`, `parse-fail`, `semantic-fail`, `refusal`, `timeout`
- [x] T028 [US2] Add argument validation hook to classify `parse-fail` before tool execution
- [x] T029 [US2] Ensure timeout exceptions are caught and logged with `outcome: "timeout"`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Record Provider Escalation and Cost Metadata (Priority: P2)

**Goal**: Telemetry for partner-model adapter and cost-sharing logic

**Independent Test**: Configure multiple providers, trigger escalation, inspect `providers.jsonl`

### Tests for User Story 3

- [x] T030 [P] [US3] Unit test: failed Ollama attempt + successful Claude attempt both recorded in `tests/unit/test_diagnostics_providers.py`
- [x] T031 [P] [US3] Unit test: cache-hit indicator present when response is cached in `tests/unit/test_diagnostics_providers.py`
- [x] T032 [P] [US3] Unit test: local model cost is `null` but latency populated in `tests/unit/test_diagnostics_providers.py`
- [x] T033 [P] [US3] Integration test: synthetic escalation chain appears with ≥2 provider lines in `tests/integration/test_diagnostics_providers.py`

### Implementation for User Story 3

- [x] T034 [US3] Instrument provider adapters in `agent/` to emit `lm_call` events to `providers.jsonl`
  - Fields: `provider`, `model`, `request_size`, `response_size`, `latency_ms`, `cost`, `cache_hit`, `escalation_node`
- [x] T035 [US3] Record each attempted provider in escalation chain, including final responder
- [x] T036 [US3] Ensure cost is `null` for local (Ollama) models

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Thermal Sampling and Security Stream Isolation (Priority: P3)

**Goal**: Thermal data for power-mode watchdog; security stream isolation

**Independent Test**: Verify `thermal.jsonl` grows at 5-second intervals; `security.jsonl` permissions are `0600`

### Tests for User Story 4

- [x] T037 [P] [US4] Unit test: `thermal.jsonl` line includes `cpu_temp`, `gpu_temp`, `power_mode` in `tests/unit/test_diagnostics_thermal.py`
- [x] T038 [P] [US4] Unit test: throttling flags parsed into `throttled: true` and bitmask in `tests/unit/test_diagnostics_thermal.py`
- [x] T039 [P] [US4] Unit test: `security.jsonl` created with mode `0600` in `tests/unit/test_diagnostics_security.py`
- [x] T040 [P] [US4] Integration test: `logs export --exclude security` excludes `security.jsonl` in `tests/integration/test_logs_cli.py`

### Implementation for User Story 4

- [x] T041 [US4] Start `ThermalSampler` background thread from `DiagnosticsLogger.__init__` when `tegrastats` is available
- [x] T042 [US4] Write `thermal.jsonl` events with `cpu_temp`, `gpu_temp`, `power_mode`, `throttled`, `throttle_flags`
- [x] T043 [US4] Ensure `/sec` kit writes findings to `security.jsonl` via `DiagnosticsLogger.log("security", ...)`
- [x] T044 [US4] Implement `hermes-lite logs export --exclude security` in `hermes_cli/logs_lite.py`
- [x] T045 [US4] Add warning when filesystem ignores POSIX permissions (FAT/exfat); rely on directory `0700`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Edge cases, safety, performance, and final integration

- [x] T046 Verify read-only filesystem degradation: disabled stream, single warning to `errors.log`
- [x] T047 Verify clock jump backward across rotation boundary uses filesystem mtime
- [x] T048 Verify 1 GB safety cap stops appending and warns per stream
- [x] T049 Verify `tegrastats` absence on non-Jetson does not crash agent
- [x] T050 Verify no raw API key appears in any JSONL stream (grep trap test)
- [x] T051 Verify daily rotation creates new file at 00:00 UTC
- [x] T052 Verify retention cleaner removes 91-day-old synthetic file but preserves 1-day-old file
- [x] T053 Verify CLI helper returns filtered results in under 1 second for 10,000-line stream
- [x] T054 Verify agent startup time increase is under 200 ms with diagnostics initialized
- [x] T055 Verify upstream plain-text logs (`agent.log`, `errors.log`, `gateway.log`) remain unchanged
- [x] T056 Verify `api.jsonl` records `azure-api` endpoint calls including partner-vs-paid routing decision
- [x] T057 Verify `workspace.jsonl` records `workspace.*` calls with repo, files touched, byte delta, budget, pre-commit result, commit SHA
- [x] T058 [P] Run retained unit-test suite and confirm zero regressions in logging, agent startup, or CLI commands
- [ ] T059 Update `REDESIGN.md` §5.14 references to reflect completed implementation
- [ ] T060 Update `specs/012-diagnostics-logging/` status to Complete

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) — Builds on US1 instrumentation but can be tested standalone
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) — Builds on US1+US2 but can be tested standalone with mocked provider calls
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) — Orthogonal to US1-US3; thermal and security are independent

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Schema before stream writer
- Stream writer before consumer instrumentation
- Core implementation before CLI helper
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- US1 (agent stream) and US4 (thermal/security) are orthogonal and can proceed in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (agent lifecycle events + CLI helper)
4. **STOP and VALIDATE**: Start a session, verify `agent.jsonl` contains `kit_load`, query via `hermes-lite logs --stream agent --since today --tail 20`
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
   - Developer A: User Story 1 (agent stream + CLI)
   - Developer B: User Story 2 (tools stream)
   - Developer C: User Story 3 (providers stream)
   - Developer D: User Story 4 (thermal + security streams)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- `security.jsonl` MUST be created with mode `0600`; exports MUST exclude it by default
- Secret redaction MUST run on every payload before JSON serialization
- Daily rotation MUST use filesystem mtime, not monotonic time
- Retention cleanup MUST skip `.archive` suffix and `archive/` subdirectory
- The upstream plain-text logs (`agent.log`, `errors.log`, `gateway.log`) MUST remain unchanged
