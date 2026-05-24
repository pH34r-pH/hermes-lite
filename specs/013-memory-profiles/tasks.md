# Tasks: Memory Profiles per Workflow

**Input**: Design documents from `/specs/013-memory-profiles/`

**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Tests are included as specified in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Module scaffold, config schema extension, upstream integration verification

- [x] T001 Create `plugins/memory/profiles.py` with module docstring and class stubs (`MemoryProfile`, `ProfileBinding`, `SecurityProfileGuard`, `CompositeRecallQuery`)
- [x] T002 Verify `plugins/memory/__init__.py` exists; document provider adapter interface integration point
- [x] T003 Verify `plugins/memory/honcho/__init__.py` exists; document namespace mapping integration point
- [x] T004 Verify `plugins/memory/retaindb/__init__.py` exists; document table-prefix mapping integration point
- [x] T005 Verify `agent/tool_surface.py` exists; document kit transition hook integration point
- [x] T006 Verify `agent/diagnostics.py` exists; document `profile_switch` event emission integration point
- [x] T007 Add `memory_profiles.bindings` schema stub to `~/.hermes-lite/lite-config.yaml` documentation / template
  - Document eight canonical profiles and kit→profile mappings
- [x] T008 [P] Add CLI subcommand registration stubs in `hermes_cli/commands.py` for `memory --profile` and `memory --list-profiles`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T009 Implement `MemoryProfile` dataclass in `plugins/memory/profiles.py`
  - Eight canonical names: `research`, `spec`, `dev`, `web`, `azure`, `infra`, `api`, `security`
  - Lower-case alphanumeric validation
- [x] T010 Implement `ProviderNamespaceMap` in `plugins/memory/profiles.py`
  - Translation table mapping canonical profile names to provider-specific identifiers
  - Honcho project names, mem0 namespaces, SQLite table prefixes (e.g., `research_messages`)
- [x] T011 Implement `ProfileBinding` in `plugins/memory/profiles.py`
  - Load `memory_profiles.bindings` from `~/.hermes-lite/lite-config.yaml`
  - Support single and multi-profile bindings per kit
  - Validate kit and profile names; reject unknown mappings with warning and fallback to `dev`
- [x] T012 Implement `SecurityProfileGuard` in `plugins/memory/profiles.py`
  - Write-only access for `/sec` kit on `security` profile
  - Read-only access for all other kits
  - Raise `MemoryWriteDenied` on unauthorized write attempt
- [x] T013 Implement `CompositeRecallQuery` in `plugins/memory/profiles.py`
  - Query all bound profiles for a composite kit
  - Merge and rank results with per-profile relevance weighting
  - In-flight queries complete against the profile they were started with
- [x] T014 Update `plugins/memory/__init__.py` to wrap provider load/save/recall calls
  - Inject profile namespace translation before provider call
  - Apply `SecurityProfileGuard` before writes
  - Route composite kit queries through `CompositeRecallQuery`
- [x] T015 [P] Create `MemoryWriteDenied` exception class in `plugins/memory/profiles.py`

**Checkpoint**: Foundation ready — profile definitions, namespace map, bindings, security guard, composite recall, and provider wrapper exist; user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Load a Kit and Switch Memory Profile (Priority: P1) 🎯 MVP

**Goal**: Isolating memory by workflow reduces retrieval noise on a 3B model

**Independent Test**: Load arXiv kit, store a note, switch to azure-ops, verify note is not visible in recall

### Tests for User Story 1

- [x] T016 [P] [US1] Unit test: loading `arxiv` kit sets active profile to `research` in `tests/unit/test_memory_profiles.py`
- [x] T017 [P] [US1] Unit test: `agent.jsonl` contains `profile_switch` event with correct `profile` field in `tests/unit/test_memory_profiles.py`
- [x] T018 [P] [US1] Unit test: default profile at startup is `dev` in `tests/unit/test_memory_profiles.py`
- [x] T019 [P] [US1] Integration test: stored note in `research` is not returned after switching to `azure` in `tests/integration/test_memory_profiles.py`

### Implementation for User Story 1

- [x] T020 [US1] Add kit transition hook in `agent/tool_surface.py` to call `ProfileBinding.resolve(kit_name)`
- [x] T021 [US1] Emit `profile_switch` event from kit transition hook via `agent/diagnostics.py`
  - Payload: old profile list, new profile list, kit name
- [x] T022 [US1] Ensure `run_agent.py` passes active profile set into memory provider wrapper
- [x] T023 [US1] Implement `hermes-lite memory --profile` CLI in `hermes_cli/commands.py` to display active profile
- [x] T024 [US1] Implement `hermes-lite memory --list-profiles` CLI to list eight canonical profiles and active kit bindings

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Security Profile Write Isolation (Priority: P1)

**Goal**: Prevent non-security kits from overwriting security findings

**Independent Test**: Write a finding from `/sec`, switch kits, assert write is rejected for non-security kits

### Tests for User Story 2

- [x] T025 [P] [US2] Unit test: `/sec` kit write to `security` succeeds in `tests/unit/test_security_profile.py`
- [x] T026 [P] [US2] Unit test: `spec-kit` write to `security` raises `MemoryWriteDenied` in `tests/unit/test_security_profile.py`
- [x] T027 [P] [US2] Unit test: `spec-kit` recall query returns security entries read-only in `tests/unit/test_security_profile.py`
- [x] T028 [P] [US2] Unit test: `security_refusal` event logged on unauthorized write attempt in `tests/unit/test_security_profile.py`
- [x] T029 [P] [US2] Integration test: non-security kit mutation of security profile is blocked in `tests/integration/test_security_profile.py`

### Implementation for User Story 2

- [x] T030 [US2] Integrate `SecurityProfileGuard.check_write(kit, profile)` into `plugins/memory/__init__.py` write path
- [x] T031 [US2] Emit `security_refusal` event via `agent/diagnostics.py` when `MemoryWriteDenied` is raised
- [x] T032 [US2] Surface `MemoryWriteDenied` error to gateway / CLI with clear refusal message
- [x] T033 [US2] Ensure curator reads span all profiles but writes are restricted to `spec` or session-scratch space

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Multi-Profile Binding for Composite Kits (Priority: P2)

**Goal**: Composite kits need bounded context from multiple domains

**Independent Test**: Load azure-ops, store distinct notes in azure and infra, verify recall returns both

### Tests for User Story 3

- [x] T034 [P] [US3] Unit test: `azure-ops` kit binds to `azure` and `infra` profiles in `tests/unit/test_composite_profiles.py`
- [x] T035 [P] [US3] Unit test: write from composite kit routes to primary profile unless annotated in `tests/unit/test_composite_profiles.py`
- [x] T036 [P] [US3] Unit test: recall query merges results from both bound profiles in `tests/unit/test_composite_profiles.py`
- [x] T037 [P] [US3] Unit test: no unrelated profile entries pollute composite recall in `tests/unit/test_composite_profiles.py`
- [x] T038 [P] [US3] Integration test: composite recall ranks azure higher than infra for deploy-related query in `tests/integration/test_composite_profiles.py`

### Implementation for User Story 3

- [x] T039 [US3] Implement primary/secondary profile annotation in `plugins/memory/profiles.py`
  - Default write target is primary profile; allow explicit annotation for secondary
- [x] T040 [US3] Implement per-profile relevance weighting in `CompositeRecallQuery.merge_results()`
- [x] T041 [US3] Update `ProfileBinding` to support ordered multi-profile lists for composite kits
- [x] T042 [US3] Ensure `agent.jsonl` logs full bound profile list on composite kit load

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Profile Persistence and Cross-Session Recall (Priority: P2)

**Goal**: Memory must survive agent restarts and reboots

**Independent Test**: Store a note in `spec`, restart agent, load spec-kit, verify note is recallable

### Tests for User Story 4

- [x] T043 [P] [US4] Unit test: Honcho adapter uses profile name as project identifier in `tests/unit/test_profile_persistence.py`
- [x] T044 [P] [US4] Unit test: retaindb adapter prefixes table with profile name in `tests/unit/test_profile_persistence.py`
- [x] T045 [P] [US4] Unit test: profile-persisted note survives simulated restart in `tests/unit/test_profile_persistence.py`
- [x] T046 [P] [US4] Integration test: recall after agent restart returns only correct profile entries in `tests/integration/test_profile_persistence.py`

### Implementation for User Story 4

- [x] T047 [US4] Ensure `ProviderNamespaceMap` persists mappings across process restarts (static / config-driven)
- [x] T048 [US4] Verify Honcho provider uses profile as project/namespace identifier
- [ ] T049 [US4] Verify retaindb provider prefixes table names with profile name
- [ ] T050 [US4] Add fallback namespace emulation for flat-file backends: prefix keys or store `profile` column
- [ ] T051 [US4] Document provider-specific namespace configuration in `lite-config.yaml` comments

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Edge cases, config validation, curator integration, and final validation

- [ ] T052 Verify in-flight recall queries complete against original profile after kit switch
- [ ] T053 Verify invalid kit→profile mappings in `lite-config.yaml` trigger startup warning and fallback to `dev`
- [ ] T054 Verify curator reads span all profiles in under 3 seconds for 1,000-entry test dataset
- [ ] T055 Verify curator never writes to `security` profile
- [ ] T056 Verify shared profiles (multiple kits bound to `dev`) allow writes from any bound kit
- [ ] T057 Verify `MemoryWriteDenied` is raised for all non-`/sec` kits including composite kits that include `security` as read-only
- [ ] T058 Verify profile switch event in `agent.jsonl` includes both old and new profile lists
- [ ] T059 Verify `hermes-lite memory --list-profiles` returns all eight profiles and bindings in under 1 second
- [ ] T060 Verify `run_agent.py` does not crash when memory provider is disabled or unavailable; degrades to no-op
- [ ] T061 [P] Run retained unit-test suite and confirm zero regressions in memory provider loading, recall, or kit transitions
- [ ] T062 Update `REDESIGN.md` §5.7 references to reflect completed implementation
- [x] T063 Update `specs/013-memory-profiles/` status to Complete

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
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) — Builds on US1 profile switching but tests standalone
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) — Builds on US1 binding logic but can be tested standalone
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) — Integrates with US1+US3 but tests persistence independently

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Profile models before guard logic
- Guard logic before provider wrapper updates
- Provider wrapper before kit transition hooks
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- US1 (profile switching) and US4 (persistence) are orthogonal and can proceed in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (kit load + profile switch + CLI)
4. **STOP and VALIDATE**: Load arXiv kit, store note, verify active profile is `research`; query via `hermes-lite memory --profile`
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
   - Developer A: User Story 1 (profile switching + CLI)
   - Developer B: User Story 2 (security isolation)
   - Developer C: User Story 3 (composite binding + recall merging)
   - Developer D: User Story 4 (persistence + provider namespace mapping)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- The `security` profile MUST be writeable ONLY by the `/sec` kit; all other kits MUST receive read-only access
- Composite kits MUST bind to multiple profiles simultaneously; recall MUST query all bound profiles
- Invalid kit→profile mappings MUST be rejected at startup with fallback to `dev`
- In-flight memory queries MUST complete against the profile they were started with
- Profile names MUST be lower-case alphanumeric and stable across releases
