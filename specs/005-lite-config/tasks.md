# Tasks: hermes-lite Top-Level Configuration Profile

**Input**: Design documents from `/specs/005-lite-config/`

**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Baseline audit and config scaffold

- [x] T001 Audit existing config loader in `hermes_cli/config.py` — document current merge order, schema validation, and CLI flag handling
- [x] T002 Verify `~/.hermes-lite/` directory does not yet exist; document creation plan
- [ ] T003 Verify upstream `AIAgent.__init__` accepts `max_iterations`, `provider`, and `model` parameters so the lite profile can inject values
- [x] T004 Create `lite-config.yaml` scaffold at repository root with commented section headers for each config domain

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Config schema, merge logic, and removed-provider denylist that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Define `LiteConfigProfile` Pydantic model in `hermes_cli/config.py` (or a new `hermes_cli/lite_config.py` module)
  - Fields: `model`, `escalation_order`, `enabled_gateways`, `max_iterations`, `tool_call_failure_budget`, `prompt_prefix_caching`, `per_session_snapshots`, `curator`, `fail_closed`
- [x] T006 Implement `RemovedProviderDenylist` in `hermes_cli/config.py` — static set of removed providers and gateways derived from `001-gateway-cleanup` and `000-provider-cleanup`
- [x] T007 Implement config merge logic in `hermes_cli/config.py`: `lite-config.yaml` base → `~/.hermes/config.yaml` overlay → CLI flag overrides
- [x] T008 Implement `validate_merged_config(config)` in `hermes_cli/config.py` — raises `ConfigurationError` with the exact offending key whenever a removed provider or gateway is referenced
- [x] T009 Add `--profile lite` CLI flag to `hermes_cli/commands.py` (or `cli.py` if commands are defined there)
- [x] T010 Create `~/.hermes-lite/queue/` directory with `0700` permissions on first hermes-lite run
- [x] T011 Initialize `~/.hermes-lite/queue/curator.jsonl` as an empty file on first run

**Checkpoint**: Foundation ready — config model exists, merge logic works, denylist is enforced, and user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Pin Default Model and Escalation Order (Priority: P1) 🎯 MVP

**Goal**: Ship a canonical `lite-config.yaml` that pins the default inference model and defines an escalation order so local inference is always attempted first

**Independent Test**: Start `hermes-lite` with no user config and verify that the active model resolves to `ollama:ministral-3:3b` and the escalation queue is populated in the correct order

### Tests for User Story 1 (OPTIONAL) ⚠️

- [ ] T012 [P] [US1] Unit test: `load_config(profile="lite")` resolves `model` to `ollama:ministral-3:3b` when no user config exists
- [ ] T013 [P] [US1] Unit test: escalation order returned is `[ollama, copilot, openai, claude]`
- [ ] T014 [P] [US1] Unit test: user override of `model` in `~/.hermes/config.yaml` takes precedence but escalation order remains the lite chain
- [ ] T015 [P] [US1] Unit test: escalation exhausts all providers and surfaces a clear error rather than looping infinitely

### Implementation for User Story 1

- [ ] T016 [US1] Populate `lite-config.yaml` with `model: "ollama:ministral-3:3b"`
- [ ] T017 [US1] Populate `lite-config.yaml` with `escalation_order: [ollama, copilot, openai, claude]`
- [ ] T018 [US1] Implement provider escalation loop in `run_agent.py` or `agent/agent_init.py` — on failure, walk the escalation order and instantiate the next provider
- [ ] T019 [US1] Skip escalation targets that lack an API key (log at `INFO` and move to next candidate)
- [ ] T020 [US1] Surface a clear `ConfigurationError` or user-facing message when the final provider in the escalation order fails

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Declare Enabled Gateways and Disable Removed Providers Fail-Closed (Priority: P2)

**Goal**: Declare allowed gateways in `lite-config.yaml` and reject any config referencing removed providers or gateways at startup

**Independent Test**: Create a config that sets `gateway: telegram` and verify that `hermes-lite` exits with a `ConfigurationError` naming the disallowed gateway before any network calls are made

### Tests for User Story 2 (OPTIONAL) ⚠️

- [ ] T021 [P] [US2] Unit test: `enabled_gateways: [discord, openwebui, tui]` loads only those three platforms
- [ ] T022 [P] [US2] Unit test: config referencing `gateway: telegram` causes `ConfigurationError` with message naming the removed gateway
- [ ] T023 [P] [US2] Unit test: `provider: alibaba` is accepted while `provider: yuanbao` is rejected in the same merged config
- [ ] T024 [P] [US2] Unit test: runtime attempt to re-enable a removed provider is blocked and logged at `ERROR`

### Implementation for User Story 2

- [ ] T025 [US2] Populate `lite-config.yaml` with `enabled_gateways: [discord, openwebui, tui]`
- [ ] T026 [US2] Populate `lite-config.yaml` with `fail_closed: true` and a `removed_providers` section listing all deleted platforms/gateways
- [ ] T027 [US2] Update `gateway/platform_registry.py` or `gateway/config.py` to load only gateways listed in `enabled_gateways`
- [ ] T028 [US2] Update `hermes_cli/config.py` `validate_merged_config()` to check merged config (base + overlay + CLI) against the removed-provider denylist
- [ ] T029 [US2] Implement runtime provider resolver guard in `agent/agent_init.py` or `run_agent.py` — block attempts to instantiate a removed provider and log at `ERROR`
- [ ] T030 [US2] Ensure `ConfigurationError` includes the exact offending key and the file it came from (base, overlay, or CLI)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Cap Iteration Budget and Tool-Call-Failure Budget (Priority: P3)

**Goal**: Set a per-session iteration budget of 25 and a per-kit tool-call-failure budget of 3 before forced escalation

**Independent Test**: Run a task that deliberately triggers tool-call failures and verify that the agent escalates after the third failure rather than continuing to turn 25

### Tests for User Story 3 (OPTIONAL) ⚠️

- [ ] T031 [P] [US3] Unit test: `max_iterations` is capped at 25 for lite-profile sessions
- [ ] T032 [P] [US3] Unit test: per-kit tool-call-failure counter increments on error
- [ ] T033 [P] [US3] Unit test: after 3 consecutive failures, escalation to the next provider occurs before the next tool call
- [ ] T034 [P] [US3] Unit test: failure counter resets to 0 when a new provider takes over after escalation

### Implementation for User Story 3

- [ ] T035 [US3] Populate `lite-config.yaml` with `max_iterations: 25`
- [ ] T036 [US3] Populate `lite-config.yaml` with `tool_call_failure_budget: 3`
- [ ] T037 [US3] Wire `max_iterations` from merged config into `AIAgent.__init__` in `run_agent.py`
- [ ] T038 [US3] Implement per-kit tool-call-failure counter in `agent/tool_executor.py` or `run_agent.py`
  - Increment on tool-call error
  - Reset on successful tool call
  - Trigger escalation when budget is exceeded
- [ ] T039 [US3] Ensure the failure counter is reset to 0 after provider escalation
- [ ] T040 [US3] When iteration budget is exhausted mid-task, return a summary of accomplishments and a budget-exhausted note rather than silently truncating

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Deferred-Queue Curator and Background Reviewer (Priority: P4)

**Goal**: Run curator and background reviewer in deferred-queue mode with batched approval prompts

**Independent Test**: Observe that `~/.hermes-lite/queue/curator.jsonl` grows by one line per turn and that a prompt for batch approval is emitted when the file reaches 25 lines

### Tests for User Story 4 (OPTIONAL) ⚠️

- [ ] T041 [P] [US4] Unit test: each turn appends one line to `~/.hermes-lite/queue/curator.jsonl`
- [ ] T042 [P] [US4] Unit test: queue length 25 triggers a batched approval prompt in the active gateway
- [ ] T043 [P] [US4] Unit test: user approval causes all 25 jobs to be processed in a single subagent run and the queue file is truncated
- [ ] T044 [P] [US4] Unit test: 4-hour threshold triggers a batched curator pass even when queue is below 25 jobs

### Implementation for User Story 4

- [ ] T045 [US4] Populate `lite-config.yaml` with `curator.mode: deferred_queue`, `curator.threshold_jobs: 25`, `curator.threshold_hours: 4`
- [ ] T046 [US4] Implement `DeferredQueue` class in `agent/curator.py` (or a new `agent/deferred_queue.py` module)
  - Append JSONL records to `~/.hermes-lite/queue/curator.jsonl`
  - Read queue length and oldest entry timestamp on each agent loop tick
- [ ] T047 [US4] Implement threshold check in `agent/curator.py` — emit a batched approval prompt in the active gateway when `len(queue) >= 25` or `age >= 4 hours`
- [ ] T048 [US4] Implement batch processor in `agent/curator.py` — on user approval, spawn a subagent to process all queued jobs, then truncate the queue file
- [ ] T049 [US4] Implement queue rotation limit: max 500 entries, oldest dropped when limit is exceeded
- [ ] T050 [US4] Ensure deferred-queue mode wins over user config that disables the reviewer; respect the lite profile unless the user explicitly opts out of the lite profile entirely

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Logging, startup validation, backward compatibility, and final verification

- [ ] T051 Verify running `hermes-lite --profile lite` with no user config resolves `model` to `ollama:ministral-3:3b` (startup log output)
- [ ] T052 Verify a config file referencing `gateway: telegram` causes the agent to exit within 2 seconds with a clear `ConfigurationError` (pytest)
- [ ] T053 Verify the iteration budget is capped at 25 for lite-profile sessions (`assert agent.max_iterations == 25`)
- [ ] T054 Verify after 3 consecutive tool-call failures, the agent escalates to the next provider (mock provider injection test)
- [ ] T055 Verify the deferred queue file `~/.hermes-lite/queue/curator.jsonl` grows by exactly one line per turn (line count before/after test conversation)
- [ ] T056 Verify lite-profile startup log contains effective model, gateway list, and iteration budget at `INFO` level (log capture in pytest)
- [ ] T057 Verify the same binary run without `--profile lite` uses upstream defaults (model empty, max_iterations 90, all gateways enabled)
- [ ] T058 [P] Run retained config unit-test suite and confirm zero regressions for default-profile users
- [ ] T059 Update `agent/tool_surface.py` (spec 003) to read `tool_surface.removed_provider_patterns` from the merged `lite-config.yaml` rather than hardcoding patterns
- [ ] T060 Update `REDESIGN.md` §5.1 references to reflect completed implementation
- [ ] T061 Update `specs/005-lite-config/` status to Complete

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) — Builds on merged config values from US1
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) — Uses the same merged config; orthogonal to US1–US3

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Config model fields before loader integration
- Loader integration before agent-loop integration
- Core implementation before gateway/platform integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all four user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- US2 gateway validation and US4 deferred queue touch different subsystems and can run in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (`hermes-lite --profile lite` resolves correct model and escalation order)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (model pin + escalation)
   - Developer B: User Story 2 (gateway allowlist + fail-closed)
   - Developer C: User Story 3 (iteration / failure budgets)
   - Developer D: User Story 4 (deferred queue)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- The merge order is strict: `lite-config.yaml` base → `~/.hermes/config.yaml` overlay → CLI flag overrides
- Removed-provider references in the user overlay must still be rejected; the overlay does not bypass the denylist
- `~/.hermes-lite/` is the canonical home directory for the fork, distinct from `~/.hermes/`, and must be created on first run with `0700` permissions
- Backward compatibility is required: running without `--profile lite` must use upstream defaults unchanged
