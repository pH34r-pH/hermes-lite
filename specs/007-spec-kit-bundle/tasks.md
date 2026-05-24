# Tasks: Spec-Kit Skill Bundle

**Input**: Design documents from `/specs/007-spec-kit-bundle/`

**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Tests are included as specified in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Directory structure, template scaffold, and upstream integration points

- [x] T001 Create `skills/development/spec-kit/` directory tree: `spec-constitution/`, `spec-specify/`, `spec-clarify/`, `spec-plan/`, `spec-tasks/`, `spec-test/`, `spec-analyze/`, `spec-checklist/`, `spec-implement/`, `spec-review/`, `templates/`, `lib/`
- [x] T002 Create `skills/development/spec-kit/manifest.yaml` — bundle manifest exposing `/spec` slash command with sequential skill list
- [ ] T003 Verify `agent/tool_surface.py` (spec 003) kit allowlist infrastructure exists; document `spec-kit` kit registration point
- [ ] T004 Verify `plugins/local_repo_workspace/` (spec 010) exposes typed tools (`workspace.apply_patch`, `workspace.commit`, `workspace.open_pr`); document integration points
- [ ] T005 Verify `plugins/memory/` (spec 013) exposes `spec` and `dev` memory profiles; document profile binding hook
- [x] T006 Add `skills/development/spec-kit/lib/__init__.py` scaffold with module docstring and version constant
- [x] T007 [P] Create template scaffolds in `skills/development/spec-kit/templates/`:
  - `constitution.md.j2`, `spec.md.j2`, `plan.md.j2`, `tasks.md.j2`, `analyze.md.j2`, `checklist.md.j2`, `tests.md.j2`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core Python support modules and templates that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T008 Implement `ApprovalGate` class in `skills/development/spec-kit/lib/approval_gate.py`
  - Two mandatory gates: research→spec (`arxiv-write → spec-specify`) and tasks→implement (`spec-tasks → spec-implement`)
  - Emit user-confirmation prompt in originating gateway and block until response received
  - Support `approve`, `reject`, `abort` responses; abort rolls back and leaves workspace clean
  - Store gate state in `spec` memory profile for audit
- [ ] T009 Implement `SpecSeed` parser in `skills/development/spec-kit/lib/seed_parser.py`
  - Read `~/repos/knowledge/seeds/<feature>.json`
  - Validate schema: `title`, `summary`, `problem_statement`, `candidate_approach`, `citations`, `acceptance_criteria`
  - Map `target_repo` field to registered workspace via `workspaces.yaml`
  - Raise clear error when target workspace is not registered
- [ ] T010 Implement `TaskRecord` validator in `skills/development/spec-kit/lib/task_validator.py`
  - Parse `tasks.md` into structured task records
  - Fields: `task_id`, `description`, `target_subtree`, `allowed_file_globs`, `change_budget`, `pre_commit_gate`
  - DAG cycle detection using DFS/Kahn's algorithm
  - Plan-section reference validation: every task must reference an existing section in `plan.md`
- [ ] T011 Implement `WorkspaceResolver` in `skills/development/spec-kit/lib/workspace_resolver.py`
  - Read `~/.hermes-lite/workspaces.yaml`
  - Resolve natural-language target to workspace entry by `id`, `friendly_name`, or `git_url`
  - Return absolute path, default branch, allowed branch prefixes, `approval_mode`
  - Disallow cross-repo plans: if seed references multiple repos, suggest splitting into two coordinated specs
- [x] T012 Implement `skills/development/spec-kit/SKILL.md` — root bundle descriptor documenting the 10-step sequential pipeline and delegation rules
- [x] T013 [P] Populate basic templates with required section headers and Jinja2 variables:
  - `spec.md.j2` — matches upstream `specify` CLI artifact shape
  - `plan.md.j2` — architecture, contracts, risks sections
  - `tasks.md.j2` — numbered, dependency-ordered task list format
  - `constitution.md.j2` — governing principles, tone, non-negotiables

**Checkpoint**: Foundation ready — approval gates, seed parser, task validator, workspace resolver, and templates exist; user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Turn Research into a Feature Spec (Priority: P1) 🎯 MVP

**Goal**: Bridge inbound research (`spec-seed.json`) into a trackable engineering spec written into the target workspace

**Independent Test**: Place a valid `spec-seed.json` in the knowledge repo, run `spec-specify`, verify `spec.md` is created in the correct workspace with all seed fields mapped

### Tests for User Story 1

- [ ] T014 [P] [US1] Unit test: `SpecSeed` parser validates required fields and rejects malformed JSON in `tests/unit/test_seed_parser.py`
- [ ] T015 [P] [US1] Unit test: `WorkspaceResolver` maps `target_repo: azure-api` to correct absolute path in `tests/unit/test_workspace_resolver.py`
- [ ] T016 [P] [US1] Unit test: `ApprovalGate` blocks until user responds and records state in memory profile in `tests/unit/test_approval_gate.py`
- [ ] T017 [P] [US1] Integration test: end-to-end `spec-specify` produces valid `spec.md` from seed in `tests/integration/test_spec_specify.py`

### Implementation for User Story 1

- [x] T018 [US1] Write `skills/development/spec-kit/spec-constitution/SKILL.md` — skill definition for creating/updating `<workspace>/specs/constitution.md`
  - Create file if missing; update if existing
  - Populate from `constitution.md.j2` with workspace-specific tone and non-negotiables
- [x] T019 [US1] Write `skills/development/spec-kit/spec-specify/SKILL.md` — skill definition for converting seed to spec
  - Read `spec-seed.json` via `seed_parser.py`
  - Resolve target workspace via `workspace_resolver.py`
  - Trigger mandatory approval gate (research→spec) before writing
  - On approval, write `<workspace>/specs/<feature>/spec.md` from `spec.md.j2`
  - Map all seed fields: title, summary, problem_statement, candidate_approach, citations, acceptance_criteria
  - On rejection, halt and inform user no spec was written
- [ ] T020 [US1] Wire `spec-constitution` and `spec-specify` into root `SKILL.md` as steps one and two
- [ ] T021 [US1] Handle missing target workspace: refuse to write and ask user to register workspace or select alternative target
- [ ] T022 [US1] Add `spec-kit` kit allowlist entry to `agent/tool_surface_allowlists.yaml` (or equivalent spec 003 artifact)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Generate Architecture Plan and Task Breakdown (Priority: P1)

**Goal**: Produce `plan.md` with architecture, contracts, and risks; then produce dependency-ordered `tasks.md` scoped to single-repo changes

**Independent Test**: Run `spec-plan` and `spec-tasks` against a draft spec and verify `plan.md` and `tasks.md` exist, tasks reference the plan, and dependencies form a DAG

### Tests for User Story 2

- [ ] T023 [P] [US2] Unit test: `spec-plan` produces `plan.md` with architecture, contracts, and risks sections in `tests/unit/test_spec_plan.py`
- [ ] T024 [P] [US2] Unit test: `spec-tasks` produces `tasks.md` with no cyclic dependencies in `tests/unit/test_spec_tasks.py`
- [ ] T025 [P] [US2] Unit test: each task includes task ID, description, target sub-tree, allowed file globs, change budget, and pre-commit gate in `tests/unit/test_spec_tasks.py`
- [ ] T026 [P] [US2] Unit test: cross-repo plan request is rejected with suggestion to split into two specs in `tests/unit/test_workspace_resolver.py`

### Implementation for User Story 2

- [x] T027 [US2] Write `skills/development/spec-kit/spec-clarify/SKILL.md` — skill definition for targeted clarification questions
  - Generate up to five clarification questions based on spec content
  - Await user answers in originating gateway
  - Write answers back into `spec.md` under a "Clarifications" section
- [x] T028 [US2] Write `skills/development/spec-kit/spec-plan/SKILL.md` — skill definition for architecture planning
  - Read `spec.md` and `dev`/`web`/`azure`/`infra`/`api` memory profiles as needed for context
  - Produce `<workspace>/specs/<feature>/plan.md` from `plan.md.j2`
  - Include: architecture overview, component contracts, risk assessment
- [x] T029 [US2] Write `skills/development/spec-kit/spec-tasks/SKILL.md` — skill definition for task breakdown
  - Read `plan.md`
  - Produce `<workspace>/specs/<feature>/tasks.md` from `tasks.md.j2`
  - Numbered, dependency-ordered task list keyed off `plan.md` sections
  - Each task: ID, description, target sub-tree, allowed file globs, change budget (max files, max lines), pre-commit gate command
  - Validate DAG via `task_validator.py`; pause for correction on cycle detection
- [ ] T030 [US2] Wire `spec-clarify`, `spec-plan`, and `spec-tasks` into root `SKILL.md` as steps three, four, and five
- [ ] T031 [US2] Handle cross-repo plans: detect multi-repo scope, emit error, suggest linked IDs and separate `spec-seed.json` envelopes

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Gated Implementation with LocalRepoWorkspace (Priority: P2)

**Goal**: Execute tasks one-by-one through `LocalRepoWorkspace`, enforcing branch hygiene, pre-commit gates, and change budgets

**Independent Test**: Run `spec-implement` against a small feature with 2–3 tasks and verify commits appear on a topic branch, pre-commit gate ran, and workspace journal contains the diff

### Tests for User Story 3

- [ ] T032 [P] [US3] Unit test: `spec-implement` creates `hermes/<feature>` topic branch off `main` in `tests/unit/test_spec_implement.py`
- [ ] T033 [P] [US3] Unit test: pre-commit gate failure blocks commit and surfaces error in `tests/unit/test_spec_implement.py`
- [ ] T034 [P] [US3] Unit test: change-budget overflow pauses for re-approval in `tests/unit/test_spec_implement.py`
- [ ] T035 [P] [US3] Integration test: end-to-end implement for 2-task feature produces two commits on topic branch in `tests/integration/test_spec_implement.py`

### Implementation for User Story 3

- [x] T036 [US3] Write `skills/development/spec-kit/spec-test/SKILL.md` — skill definition for optional tests description
  - Read `spec.md` and `plan.md`
  - Optionally emit `<workspace>/specs/<feature>/tests.md` with executable requirements
  - Skip if user does not request tests
- [x] T037 [US3] Write `skills/development/spec-kit/spec-checklist/SKILL.md` — skill definition for verification checklist
  - Generate `checklist.md` for the active feature
  - Include acceptance criteria derived from `spec.md`
- [x] T038 [US3] Write `skills/development/spec-kit/spec-implement/SKILL.md` — skill definition for task execution
  - Trigger mandatory approval gate (tasks→implement) before starting
  - Read `tasks.md` and walk tasks one at a time
  - For each task: load appropriate kit, apply patch via `workspace.apply_patch`, run pre-commit gate, commit on topic branch
  - Create or reuse topic branch matching workspace allowed prefix (e.g., `hermes/<feature>`)
  - Never mutate `main`/`master` directly
  - Honor per-task change budget; pause for re-approval on overflow
  - On pre-commit gate failure: block commit, surface failure to gateway, ask user how to proceed
  - On allowed-file-glob mismatch: warn, skip task with note in commit message, continue to next task
  - On merge conflict during `apply_patch`: surface conflict files, offer follow-up task resolution, never auto-resolve
  - On user mid-task abort: roll back active patch (`git checkout -- .` or stash), leave workspace clean, report abort
  - Commit messages include: `Spec:`, `Task:`, `Source:`, `Session:`, `Repo:` fields
- [ ] T039 [US3] Wire `spec-test`, `spec-checklist`, and `spec-implement` into root `SKILL.md` as steps six, eight, and nine
- [ ] T040 [US3] Integrate `LocalRepoWorkspace` tool calls for `apply_patch`, `commit`, `push`, `open_pr`
- [ ] T041 [US3] Handle missing pre-commit gate command: record as `skipped` with warning; commit proceeds; PR description notes missing gate

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Consistency Analysis and Background Review (Priority: P2)

**Goal**: Validate cross-artifact consistency before implementation and invoke background reviewer before PR opening

**Independent Test**: Introduce deliberate inconsistency (task references non-existent plan section) and verify `spec-analyze` flags it; check that `spec-review` produces structured findings

### Tests for User Story 4

- [ ] T042 [P] [US4] Unit test: `spec-analyze` flags missing plan section reference in `tests/unit/test_spec_analyze.py`
- [ ] T043 [P] [US4] Unit test: `spec-analyze` emits success summary when all artifacts are consistent in `tests/unit/test_spec_analyze.py`
- [ ] T044 [P] [US4] Unit test: `spec-review` appends background-reviewer findings to workspace journal in `tests/unit/test_spec_review.py`
- [ ] T045 [P] [US4] Integration test: deliberate inconsistency is caught and loop pauses in `tests/integration/test_spec_analyze_review.py`

### Implementation for User Story 4

- [x] T046 [US4] Write `skills/development/spec-kit/spec-analyze/SKILL.md` — skill definition for cross-artifact consistency analysis
  - Read `spec.md`, `plan.md`, and `tasks.md`
  - Validate: every task ID is unique, every dependency exists, no cycles, every task references an existing plan section
  - Non-destructive: emit warnings and pause loop for correction; never mutate artifacts
  - On success: emit success summary and allow loop to proceed
- [x] T047 [US4] Write `skills/development/spec-kit/spec-review/SKILL.md` — skill definition for pre-PR review
  - Invoke background reviewer over diff set produced by `spec-implement`
  - If background reviewer is disabled: degrade gracefully to self-check (diff stats, file count, test command presence) and note degradation in PR description
  - Write structured findings (severity, file, line, recommendation) into workspace journal
  - When `workspace.open_pr` runs, ensure PR description includes `spec-analyze` results and background-reviewer findings
- [ ] T048 [US4] Wire `spec-analyze` and `spec-review` into root `SKILL.md` as steps seven and ten
- [ ] T049 [US4] Integrate background reviewer queue configuration (`curator.mode: deferred_queue`) from spec 005

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Sequential skill surfacing, memory profile binding, template validation, and final verification

- [ ] T050 Wire sequential skill loading/unloading through `agent/tool_surface.py` — only the active skill's toolset is exposed per turn
- [ ] T051 Bind the `spec-kit` kit to the `spec` and `dev` memory profiles on load (spec 013 integration)
- [ ] T052 Verify `spec-plan` produces `plan.md` within 120 seconds for single-sub-tree features (Jetson 25 W)
- [ ] T053 Verify `spec-tasks` produces a DAG with no cycles and every task referencing an existing plan section
- [ ] T054 Verify `spec-implement` never commits to `main`/`master` directly — check git log
- [ ] T055 Verify a complete spec→plan→tasks→implement cycle for a 3-task feature completes in under 15 minutes on Jetson 25 W
- [ ] T056 Verify `spec.md.j2`, `plan.md.j2`, and `tasks.md.j2` match upstream `specify` CLI artifact shapes where pattern is defined
- [ ] T057 [P] Run retained unit-test suite and confirm zero regressions in skill loading, workspace tools, or memory profiles
- [ ] T058 Update `agent/tool_surface_allowlists.yaml` with finalized `spec-kit` tool names after skill audit
- [ ] T059 Update `REDESIGN.md` §5.10, §9, §10 references to reflect completed implementation
- [ ] T060 Update `specs/007-spec-kit-bundle/` status to Complete

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) — Builds on `spec-specify` output but can be tested with a hand-written `spec.md`
- **User Story 3 (P2)**: Can start after US2 delivers `tasks.md` — Needs task records
- **User Story 4 (P2)**: Can start after US2 and US3 — Needs artifacts to analyze and diff to review

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Templates before skill markdown
- Support library before skill integration
- Core skill before integration into root SKILL.md
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 and US2 can start in parallel
- All tests for a user story marked [P] can run in parallel
- Template scaffolding (T007) and library implementation (T008–T011) can run in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (place seed, run `spec-specify`, verify `spec.md` in target workspace)
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
   - Developer A: User Story 1 (seed → spec)
   - Developer B: User Story 2 (plan + tasks)
3. Once US2 is done:
   - Developer C: User Story 3 (implementation)
   - Developer D: User Story 4 (analysis + review)
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
- The `spec-kit` kit MUST honor the per-kit tool-call-failure budget of 3 (spec 005)
- The `spec` and `dev` memory profiles MUST be bound on kit load and unbound on unload (spec 013)
- Cross-repo plans are explicitly disallowed; enforce at `spec-plan` and `spec-tasks` boundaries
- Unattended auto-promotion is never allowed; both approval gates require live user confirmation in the gateway
- `spec-implement` MUST use `LocalRepoWorkspace` as the only sanctioned mutation path (spec 010)
