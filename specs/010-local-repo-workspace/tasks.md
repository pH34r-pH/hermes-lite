# Tasks: LocalRepoWorkspace Plugin

**Input**: Design documents from `/specs/010-local-repo-workspace/`

**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Tests are included as specified in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Directory structure, module scaffolds, schema files, and upstream integration points

- [x] T001 Create `plugins/local_repo_workspace/` directory tree: `tools/`, `lib/`, `schemas/`
- [x] T002 Create `plugins/local_repo_workspace/__init__.py` with plugin entry point stub
- [x] T003 Create `plugins/local_repo_workspace/schemas/workspace_registry.schema.yaml`
  - Fields: `id`, `friendly_name`, `path`, `default_branch`, `allowed_branch_prefixes`, `push_remote`, `commit_author`, `allowed_file_globs`, `required_reviewers`, `approval_mode`
  - Document default `approval_mode: pr-only`
- [x] T004 Create `plugins/local_repo_workspace/schemas/change_journal.schema.json`
  - Fields: `step`, `session_id`, `timestamp`, `workspace_id`, `diff`, `files_changed`, `lines_changed`, `commit_sha`, `precommit_gate_result`, `pr_url`, `rejection_reason`
- [x] T005 Verify `agent/tool_guardrails.py` exists; document lowest-level safety net relationship
- [x] T006 Verify `agent/file_safety.py` exists; document path-guard layering
- [x] T007 Verify `plugins/kanban/` exists; document worktree delegation integration point
- [x] T008 [P] Add `lib/__init__.py` and `tools/__init__.py` scaffolds with module docstrings

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core Python support modules that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T009 Implement `WorkspaceRegistry` in `plugins/local_repo_workspace/registry.py`
  - Read / write `~/.hermes-lite/workspaces.yaml` with schema validation
  - On malformed or missing registry: refuse all operations and emit clear error with template path
  - CRUD operations for workspace entries
- [x] T010 Implement `WorkspaceEntry` dataclass in `plugins/local_repo_workspace/models.py`
  - Fields per schema: id, friendly_name, path, default_branch, allowed_branch_prefixes, push_remote, commit_author, allowed_file_globs, required_reviewers, approval_mode
  - Validation: path must be absolute; default_branch must not be empty
- [x] T011 Implement `GitRunner` in `plugins/local_repo_workspace/lib/git_runner.py`
  - Subprocess wrapper for git with environment scrubbing (no inherited `GIT_*` overrides)
  - Working-copy-only `git config` overrides
  - SSH agent socket pinned per workspace
  - Handle missing SSH agent socket with clear error
- [x] T012 Implement `BranchHygiene` in `plugins/local_repo_workspace/lib/branch_hygiene.py`
  - Never mutate `main`/`master` directly
  - Create or reuse topic branch matching allowed prefix off default branch
  - Verify branch name against allowed prefixes; refuse if mismatch
- [x] T013 Implement `ChangeBudget` in `plugins/local_repo_workspace/lib/change_budget.py`
  - Per-directive max files and max lines counter
  - Pause for re-approval on overage regardless of `approval_mode`
  - Return budget status to caller
- [x] T014 Implement `PreCommitGate` in `plugins/local_repo_workspace/lib/precommit_gate.py`
  - Run workspace-configured command before each commit
  - On missing command: record as `skipped` with warning; proceed but note in PR description
  - On failure: block commit, surface output, ask user how to proceed
- [x] T015 Implement `ChangeJournal` in `plugins/local_repo_workspace/lib/change_journal.py`
  - Write structured JSON entry to `~/.hermes-lite/journal/<session-id>/<step>.json`
  - Include diff, commit metadata, pre-commit gate result, timestamp
  - Record rejections with rejected hunks and reason
- [x] T016 Implement `PathGuard` in `plugins/local_repo_workspace/lib/path_guard.py`
  - Resolve all inputs against workspace root
  - Reject path traversal and symlink escapes with clear error
- [x] T017 [P] Create root `plugin.py` with plugin lifecycle (load, unload, config validation)

**Checkpoint**: Foundation ready — workspace registry, git runner, branch hygiene, change budget, pre-commit gate, change journal, and path guard exist; user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Register and List Workspaces (Priority: P1) 🎯 MVP

**Goal**: Registry is the foundation of all bounded repo access

**Independent Test**: Add a workspace to the registry and run `workspace.list` and `workspace.locate` against it

### Tests for User Story 1

- [x] T018 [P] [US1] Unit test: `WorkspaceRegistry` parses valid `workspaces.yaml` in `tests/unit/test_workspace_registry.py`
- [x] T019 [P] [US1] Unit test: `WorkspaceRegistry` refuses operations when registry is malformed in `tests/unit/test_workspace_registry.py`
- [x] T020 [P] [US1] Unit test: `workspace.locate` resolves by friendly name in under 1 second in `tests/unit/test_locate_workspace.py`
- [x] T021 [P] [US1] Unit test: ambiguous `workspace.locate` input returns clarification request in `tests/unit/test_locate_workspace.py`
- [x] T022 [P] [US1] Integration test: unregistered repo write attempt is refused in `tests/integration/test_workspace_registry.py`

### Implementation for User Story 1

- [x] T023 [US1] Implement `workspace.list` in `plugins/local_repo_workspace/tools/list.py`
  - Return all registered workspaces with metadata
- [x] T024 [US1] Implement `workspace.locate` in `plugins/local_repo_workspace/tools/locate.py`
  - Resolve natural-language target by friendly_name, git remote URL, and path basename
  - Ambiguous matches ask for clarification rather than guessing
- [x] T025 [US1] Wire both tools into `plugins/local_repo_workspace/__init__.py`
- [x] T026 [US1] Add `workspace.list` and `workspace.locate` to agent tool surface configuration

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Apply a Patch with Pre-Commit Gate and Change Budget (Priority: P1)

**Goal**: Core write path — bounded patches, pre-commit validation, and budget enforcement

**Independent Test**: Generate a small patch against a registered workspace, run `workspace.apply_patch`, and verify staging area, gate result, and journal entry

### Tests for User Story 2

- [x] T027 [P] [US2] Unit test: `workspace.apply_patch` applies valid patch within budget in `tests/unit/test_apply_patch.py`
- [x] T028 [P] [US2] Unit test: `workspace.apply_patch` rejects patch exceeding file budget and pauses for re-approval in `tests/unit/test_apply_patch.py`
- [x] T029 [P] [US2] Unit test: `workspace.apply_patch` rejects file outside allowed globs in `tests/unit/test_apply_patch.py`
- [x] T030 [P] [US2] Unit test: pre-commit gate failure blocks commit and surfaces output in `tests/unit/test_precommit_gate.py`
- [x] T031 [P] [US2] Integration test: `workspace.diff` returns unified diff scoped to allowed globs in `tests/integration/test_workspace_diff.py`

### Implementation for User Story 2

- [x] T032 [US2] Implement `workspace.status` in `plugins/local_repo_workspace/tools/status.py`
  - Report current branch, dirty state, and ahead/behind counts
  - Refuse to apply patch if tree is dirty unless user approves stash
- [x] T033 [US2] Implement `workspace.diff` in `plugins/local_repo_workspace/tools/diff.py`
  - Return unified diff of working tree or specified commit range
  - Scope to allowed file globs
- [x] T034 [US2] Implement `workspace.apply_patch` in `plugins/local_repo_workspace/tools/apply_patch.py`
  - Validate patch applies cleanly; enforce allowed file globs; stage result
  - Enforce per-workspace change budget (max files, max lines); overage pauses for re-approval
  - Run pre-commit gate; block commit on failure
  - Write journal entry on success or rejection
- [x] T035 [US2] Wire all three tools into `plugins/local_repo_workspace/__init__.py`
- [x] T036 [US2] Add `workspace.status`, `workspace.diff`, and `workspace.apply_patch` to agent tool surface configuration

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Commit, Push, and Open a PR with Branch Hygiene (Priority: P2)

**Goal**: Close the loop from gateway directive to shared code change

**Independent Test**: Run full commit-push-PR chain against a test repo and verify branch name, commit message schema, remote URL, and PR body

### Tests for User Story 3

- [x] T037 [P] [US3] Unit test: `workspace.commit` creates topic branch off main, never commits to main in `tests/unit/test_commit.py`
- [x] T038 [P] [US3] Unit test: `workspace.push` verifies remote URL matches registry before pushing in `tests/unit/test_push.py`
- [x] T039 [P] [US3] Unit test: `workspace.push` handles non-fast-forward with rebase and surfaces conflicts in `tests/unit/test_push.py`
- [x] T040 [P] [US3] Unit test: `workspace.open_pr` produces PR body with gateway link and diff stats in `tests/unit/test_open_pr.py`
- [x] T041 [P] [US3] Integration test: full edit-commit-push-PR cycle completes in under 2 minutes in `tests/integration/test_commit_push_pr.py`

### Implementation for User Story 3

- [x] T042 [US3] Implement `workspace.commit` in `plugins/local_repo_workspace/tools/commit.py`
  - Create or reuse topic branch matching allowed prefix; never mutate `main`/`master`
  - Write schema-validated commit message: summary line, optional body, `Source:`, `Session:`, `Author-Identity:` fields
- [x] T043 [US3] Implement `workspace.push` in `plugins/local_repo_workspace/tools/push.py`
  - Push topic branch to registered remote using workspace-pinned SSH agent socket
  - Verify remote URL matches registry; refuse on mismatch
  - Handle non-fast-forward: attempt `git pull --rebase`, replay commit, stop on conflicts
  - Never pass `--force`
- [x] T044 [US3] Implement `workspace.open_pr` in `plugins/local_repo_workspace/tools/open_pr.py`
  - Open PR using GitHub CLI or REST API fallback
  - Body includes link to originating gateway message, diff statistics, and session ID
  - If `approval_mode` is `pr-only`, report PR URL to gateway
- [x] T045 [US3] Wire all three tools into `plugins/local_repo_workspace/__init__.py`
- [x] T046 [US3] Add `workspace.commit`, `workspace.push`, and `workspace.open_pr` to agent tool surface configuration

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Structured Change Journal and Audit Replay (Priority: P2)

**Goal**: Auditability — canonical record of what the agent did, when, and why

**Independent Test**: Run a workspace write sequence and inspect journal directory for expected JSON files

### Tests for User Story 4

- [x] T047 [P] [US4] Unit test: `ChangeJournal` writes entry with diff, commit SHA, gate result, timestamp in `tests/unit/test_change_journal.py`
- [x] T048 [P] [US4] Unit test: patch rejection is recorded with rejected hunks and reason in `tests/unit/test_change_journal.py`
- [ ] T049 [P] [US4] Integration test: journal directory contains one JSON per step after a session in `tests/integration/test_change_journal.py`
- [ ] T050 [P] [US4] Integration test: journal query returns summary of files touched and PR links in `tests/integration/test_change_journal.py`

### Implementation for User Story 4

- [ ] T051 [US4] Integrate `ChangeJournal.write()` calls into `workspace.apply_patch`, `workspace.commit`, and `workspace.push`
  - Success path: record diff, commit metadata, gate result, timestamp
  - Rejection path: record rejected hunks and reason
- [ ] T052 [US4] Add journal query helper to `plugins/local_repo_workspace/lib/change_journal.py`
  - Summarize files touched, lines changed, and PR links for a session ID
- [ ] T053 [US4] Ensure `workspace.apply_patch` writes journal entries before returning to caller
- [ ] T054 [US4] Verify background reviewer can read journal and produce findings referencing exact step numbers and file paths

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T055 Verify path-traversal and symlink-escape attempts are rejected in integration testing
- [ ] T056 Verify force-push is disabled — `workspace.push` never passes `--force`
- [ ] T057 Verify default `approval_mode` for new workspaces is `pr-only`
- [ ] T058 Verify unregistered repos are read-only and writes are refused with registration instructions
- [ ] T059 Verify `workspace.commit` never mutates `main`/`master` directly in integration testing
- [ ] T060 Verify budget overage ALWAYS requires re-approval regardless of `approval_mode`
- [ ] T061 Verify `GitRunner` environment scrubbing removes inherited `GIT_*` variables
- [ ] T062 Verify `workspace.push` uses workspace-pinned SSH agent socket
- [ ] T063 Integrate kanban plugin worktree delegation: when kanban creates a worktree, `LocalRepoWorkspace` delegates file operations to worktree path while enforcing same registry constraints
- [ ] T064 [P] Run retained unit-test suite and confirm zero regressions in skill loading, tool registry, or git operations
- [ ] T065 Update agent tool surface configuration with finalized `workspace.*` tool names after audit
- [ ] T066 Update `REDESIGN.md` §5.9, §9 references to reflect completed implementation
- [x] T067 Update `specs/010-local-repo-workspace/` status to Complete

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
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) — Builds on US1 registry but can be tested standalone
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) — Needs git remote and SSH setup for integration testing
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) — Integrates with US2 and US3 but can be tested standalone with mocked journal

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints (tools)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- US1 (registry) and US4 (journal) are largely orthogonal and can proceed in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (register and list workspaces)
4. **STOP and VALIDATE**: Test `workspace.list` and `workspace.locate` independently — verify registry parsing and locate resolution
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
   - Developer A: User Story 1 (registry) + User Story 2 (patch + gate)
   - Developer B: User Story 3 (commit + push + PR)
   - Developer C: User Story 4 (journal + audit)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Default `approval_mode` for new workspaces MUST be `pr-only`
- `main`/`master` MUST never be mutated directly; topic branches MUST use allowed prefixes
- Budget overage ALWAYS requires re-approval, regardless of `approval_mode`
- Force-push and history-rewrite operations MUST be disabled
- Git subprocesses MUST execute with environment scrubbing and workspace-pinned SSH agent socket
- Path traversal and symlink escape attempts MUST be rejected
- Unregistered repos MUST be read-only; the plugin MUST refuse writes and instruct the user to register
