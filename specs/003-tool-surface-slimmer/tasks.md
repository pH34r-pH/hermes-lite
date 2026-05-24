# Tasks: Tool-Surface Slimmer

**Input**: Design documents from `/specs/003-tool-surface-slimmer/`

**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Baseline verification and module scaffold

- [ ] T001 Verify `tools.registry` exposes `get_definitions()`, `register()`, and `_generation` counter semantics upstream
- [ ] T002 Verify `lite-config.yaml` (spec 005) is loadable and has a `tool_surface.removed_provider_patterns` key path, or document dependency on spec 005 completion
- [x] T003 Create `agent/tool_surface.py` scaffold with module docstring, imports (`hashlib`, `json`, `logging`, `typing`, `importlib.util`, `ast`)
- [ ] T004 [P] Create `agent/tool_surface_allowlists.yaml` scaffold with kit names (`arxiv`, `spec-kit`, `dev`, `web-ops`, `azure-ops`, `security`, `hermes-lite-core`) and empty ordered allowlists

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data structures and registry integration that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete
- [x] T005 Create `ToolSurface` class in `agent/tool_surface.py` with `__init__(active_kit: str, allowlist_path: str)`
- [x] T006 Implement `KitAllowlist` loader in `agent/tool_surface.py` — parse `agent/tool_surface_allowlists.yaml` into a dict mapping kit names to ordered lists of tool names; expose `reload()` for hot-reload
- [x] T007 Implement `ToolSurface.get_registry_schemas()` in `agent/tool_surface.py` — call `tools.registry.get_definitions()` and return the full schema list
- [x] T008 Implement `ToolSurface._filter_by_kit(schemas, kit_name)` in `agent/tool_surface.py` — retain only schemas whose `name` is in the kit allowlist; warn and skip missing or unknown tool names rather than crashing
- [x] T009 Implement `ToolSchemaDigest` helper in `agent/tool_surface.py` — canonical JSON serialization of a schema list (sorted by tool name, deterministic key ordering, no timestamps)
- [x] T010 Implement `ProviderDenylist` loader in `agent/tool_surface.py` — read `lite-config.yaml` key `tool_surface.removed_provider_patterns` into a list of module path patterns
- [x] T011 Create `ProviderRemovedError` exception class in `agent/tool_surface.py`

**Checkpoint**: Foundation ready — `ToolSurface` class exists, allowlist and denylist are loadable, and user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Expose Only Active Kit Tools (Priority: P1) 🎯 MVP

**Goal**: Construct the tool schema sent to the model from exactly one active kit rather than the full Hermes core tool surface

**Independent Test**: Start an agent with `active_kit="arxiv"`, request tool definitions, and verify that only tools listed in the arxiv kit allowlist are present

### Tests for User Story 1 (OPTIONAL) ⚠️

- [ ] T012 [P] [US1] Unit test: `ToolSurface.get_definitions("arxiv")` returns only allowed tools
- [ ] T013 [P] [US1] Unit test: `ToolSurface.get_definitions("dev")` excludes arxiv-specific tools (`arxiv-discover`, `arxiv-fetch`, `arxiv-skim`)
- [ ] T014 [P] [US1] Unit test: missing `active_kit` falls back to `hermes-lite-core` default kit
- [ ] T015 [P] [US1] Unit test: kit switch from `arxiv` to `spec-kit` changes the returned schema list

### Implementation for User Story 1
- [x] T016 [US1] Implement `ToolSurface.get_definitions(active_kit: str) -> list` in `agent/tool_surface.py`
  - Load full registry schemas via `tools.registry.get_definitions()`
  - Filter by `KitAllowlist` for the requested kit
  - Apply each tool's `check_fn` if present; omit tools where `check_fn` returns `False`
  - Return empty list rather than crashing when allowlist is empty or all tools fail `check_fn`
- [x] T017 [US1] Implement kit-switch invalidation in `agent/tool_surface.py` — when `active_kit` changes, clear cached digest and rebuild schema
- [ ] T018 [US1] Populate `agent/tool_surface_allowlists.yaml` with real tool names for `arxiv`, `spec-kit`, `dev`, and `hermes-lite-core` kits
- [ ] T019 [US1] Wire `ToolSurface.get_definitions()` into `run_agent.py` or `model_tools.py` so that the agent loop calls it instead of the raw registry

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validate Tool Schemas Against Per-Kit Allowlist (Priority: P2)

**Goal**: Validate every tool schema against the hand-curated allowlist and drop unknown tools with a warning

**Independent Test**: Register a mock tool at runtime and confirm it does not appear in the schema when the active kit's allowlist does not contain it

### Tests for User Story 2 (OPTIONAL) ⚠️

- [ ] T020 [P] [US2] Unit test: mock tool absent from `arxiv` allowlist is excluded with a logged warning
- [ ] T021 [P] [US2] Unit test: `spec-kit` allowlist returns exactly the four expected tools and no others
- [ ] T022 [P] [US2] Unit test: schema missing required `name` field is rejected with an error log naming the offending schema
- [ ] T023 [P] [US2] Unit test: hot-reloading the allowlist file applies changes without a process restart

### Implementation for User Story 2
- [x] T024 [US2] Implement `ToolSurface.validate(schema, kit_allowlist)` in `agent/tool_surface.py`
  - Check that `schema` contains `name`, `description`, and `parameters`
  - Check that `schema["name"]` is present in the kit allowlist
  - Return `True`/`False`; caller logs at `WARNING` on `False`
- [ ] T025 [US2] Integrate `validate()` into `get_definitions()` so each schema is validated before inclusion
- [ ] T026 [US2] Implement `KitAllowlist.reload()` in `agent/tool_surface.py` — re-read `agent/tool_surface_allowlists.yaml` from disk and update the in-memory mapping
- [ ] T027 [US2] Add structural schema validation: reject schemas missing `name`, `description`, or `parameters`; log the schema index or truncated representation

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Emit Static Cache-Friendly Digest (Priority: P3)

**Goal**: Compute a deterministic digest of the active tool schema so upstream prefix caches can reuse KV state across turns

**Independent Test**: Call `tool_surface.digest()` twice with the same kit and compare; then mutate a tool description and confirm the digest changes

### Tests for User Story 3 (OPTIONAL) ⚠️

- [ ] T028 [P] [US3] Unit test: successive `digest()` calls with identical kit return identical strings
- [ ] T029 [P] [US3] Unit test: patching a tool description changes the digest
- [ ] T030 [P] [US3] Unit test: switching from kit `A` to kit `B` yields a different digest
- [ ] T031 [P] [US3] Unit test: digest is attached to API request metadata (or agent instance) as a stable identifier

### Implementation for User Story 3
- [x] T032 [US3] Implement `ToolSurface.digest() -> str` in `agent/tool_surface.py`
  - Serialize the current filtered schema list via `ToolSchemaDigest` canonical JSON
  - Compute SHA-256 over the serialized bytes
  - Return hex digest string
- [x] T033 [US3] Implement digest cache keyed by `(active_kit, registry_generation)` in `agent/tool_surface.py`
  - Cache the digest after first computation
  - Invalidate when `tools.registry._generation` changes or when `active_kit` changes
- [ ] T034 [US3] Ensure the digest changes when a tool's `check_fn` result changes at runtime (i.e., digest reflects the runtime-available subset)
- [ ] T035 [US3] Attach the digest to the agent's API request metadata (e.g., header or internal tracking) so cache layers can key on it

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Refuse to Load Tools Importing Removed Providers (Priority: P4)

**Goal**: Inspect each tool module's import graph at load time and reject any tool that transitively imports a removed provider module

**Independent Test**: Attempt to register a tool that imports `gateway.platforms.telegram` and confirm it is rejected before any schema is emitted

### Tests for User Story 4 (OPTIONAL) ⚠️

- [ ] T036 [P] [US4] Unit test: tool with top-level `import gateway.platforms.telegram` raises `ProviderRemovedError`
- [ ] T037 [P] [US4] Unit test: tool transitively importing a removed provider via a utility module is rejected and log names the import chain
- [ ] T038 [P] [US4] Unit test: tool importing only allowed modules is accepted and surfaced normally
- [ ] T039 [P] [US4] Unit test: adding a new denylist pattern in `lite-config.yaml` causes matching tools to be rejected on next agent init

### Implementation for User Story 4
- [x] T040 [US4] Implement `ToolSurface.scan_imports(module) -> list` in `agent/tool_surface.py`
  - Use `ast` to parse the module's source and extract top-level `import` and `from ... import` statements
  - Return a flat list of imported module path strings
  - Document that lazy imports inside functions are out of scope for v1
- [x] T041 [US4] Implement depth-limited transitive import scan in `agent/tool_surface.py`
  - For each top-level import, resolve the module file and recurse up to a configurable depth limit (default 3)
  - Record the import chain for diagnostics
- [x] T042 [US4] Implement `ToolSurface._check_removed_providers(import_chain)` in `agent/tool_surface.py`
  - Match each imported module path against `ProviderDenylist` patterns
  - Raise `ProviderRemovedError` on first match; include the offending import chain in the message
- [ ] T043 [US4] Integrate import scanning into `ToolSurface.get_definitions()` or registry hook so that scanned tools are rejected before their schema is included
- [ ] T044 [US4] Ensure `ProviderRemovedError` is caught at an appropriate boundary and logged at `ERROR` level without crashing the agent

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Integration, static analysis, and final verification

- [ ] T045 Verify `agent/tool_surface.py` has no direct import of `model_tools.py` or `run_agent.py` (static import graph analysis)
- [ ] T046 Verify agent startup with `active_kit="dev"` completes in under 500 ms on Jetson Orin Nano (`time hermes-lite --kit dev --dry-run`)
- [ ] T047 Verify `len(tool_surface.get_definitions("arxiv")) <= 12`
- [ ] T048 Verify digest for the same kit on two successive turns is identical
- [ ] T049 [P] Run retained unit-test suite and confirm zero regressions in `tools.registry` or agent initialization
- [ ] T050 [P] Update `agent/tool_surface_allowlists.yaml` with finalized tool names for all kits after registry audit
- [ ] T051 Update `REDESIGN.md` §5.6 references to reflect completed implementation
- [ ] T052 Update `specs/003-tool-surface-slimmer/` status to Complete

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) — Builds on allowlist infrastructure from US1
- **User Story 3 (P3)**: Can start after US1 — Requires filtered schema list to compute digest over
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) — Independent of US1–US3 but integrates at `get_definitions()` boundary

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Validation logic before integration into `get_definitions()`
- Core implementation before integration with agent loop
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1, US2, and US4 can start in parallel
- US3 can start as soon as US1 delivers a working `get_definitions()`
- All tests for a user story marked [P] can run in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (active_kit=arxiv returns <=12 tools)
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
   - Developer A: User Story 1 (kit filtering)
   - Developer B: User Story 2 (schema validation)
   - Developer C: User Story 4 (import scanning)
3. Once US1 is done:
   - Developer D: User Story 3 (digest emitter)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- `agent/tool_surface.py` MUST NOT import `model_tools.py` or `run_agent.py`; the dependency arrow points upward only
- Lazy imports inside functions are a known v1 gap; document this limitation in module docstring
