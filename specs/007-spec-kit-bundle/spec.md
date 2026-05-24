# Feature Specification: Spec-Kit Skill Bundle

**Feature Branch**: `007-spec-kit-bundle`

**Created**: 2026-05-24

**Status**: Draft

**Input**: User description: "New skills/development/spec-kit/ bundle implementing spec→plan→tasks→implement pattern with 10 sequential skills (spec-constitution through spec-review). LocalRepoWorkspace integration, approval gates. Read REDESIGN.md §5.10, §9, §10."

## Current State

Upstream Hermes Agent ships extensive `software-development/`, `github/`, and `devops/` skills for code editing, linting, testing, and git operations. However, there is **no spec-driven development bundle** that guides the agent through a structured `spec.md → plan.md → tasks.md → implement` workflow. Hermes can edit files and commit changes, but it has no native skills for: writing a `constitution.md`, specifying a feature spec, asking clarification questions, generating architecture plans, breaking work into dependency-ordered tasks, analyzing cross-artifact consistency, generating checklists, or executing tasks through a gated workspace commit pipeline. There is no concept of a `spec-seed.json` hand-off from research output, no mandatory approval gate between planning and implementation, and no integration between the spec process and the background reviewer / security kit.

The upstream `specify` CLI (https://github.com/github/spec-kit) codifies the spec-driven development pattern, but Hermes-lite does not depend on it at runtime. Instead, hermes-lite ships native skills that produce the same artifact shapes while remaining fully operable offline on the Jetson.

## Target State

Hermes-lite ships a complete `skills/development/spec-kit/` bundle exposed through a `/spec` slash command. The bundle implements 10 sequential skills, each sized for a 3B model context, each producing or consuming the standard spec-kit artifacts (`spec.md`, `plan.md`, `tasks.md`, `analyze.md`, `checklist.md`, `tests.md`, `constitution.md`). The bundle integrates with `LocalRepoWorkspace` (§5.9) for all file mutations and git operations. Two mandatory approval gates protect auto-promotion: one at the `arxiv-write → spec-specify` boundary (research to spec) and one at the `spec-tasks → spec-implement` boundary (planning to implementation). The bundle reads and writes into any registered workspace, with cross-repo plans explicitly disallowed at the planning step. The final `spec-review` skill invokes the background reviewer over the diff set before a PR is opened.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Turn Research into a Feature Spec (Priority: P1)

A user has completed an arXiv research session that produced `~/repos/knowledge/seeds/my-feature.json`. The user confirms promotion, and `spec-specify` reads the seed, binds to the target workspace, and writes `specs/my-feature/spec.md` following the spec template format.

**Why this priority**: This is the bridge between inbound research and outbound implementation. Without it, research notes cannot be converted into trackable engineering work.

**Independent Test**: Can be fully tested by placing a valid `spec-seed.json` in the knowledge repo, running `spec-specify`, and verifying that `spec.md` is created in the correct workspace with all seed fields mapped.

**Acceptance Scenarios**:

1. **Given** a `spec-seed.json` exists at `knowledge/seeds/my-feature.json`, **When** the user confirms promotion in the gateway, **Then** `spec-specify` reads the seed and writes `<target-workspace>/specs/my-feature/spec.md`
2. **Given** the seed names `target_repo: azure-api`, **When** `spec-specify` runs, **Then** the spec is written into `~/repos/azure-api/specs/my-feature/spec.md`
3. **Given** the seed names `target_repo: hermes-lite`, **When** `spec-specify` runs, **Then** the spec is written into `~/repos/hermes-lite/specs/my-feature/spec.md`
4. **Given** the user does not confirm promotion, **When** the approval gate is reached, **Then** no spec is written and the agent waits for user input

---

### User Story 2 - Generate Architecture Plan and Task Breakdown (Priority: P1)

After a spec is written, `spec-plan` produces `plan.md` with architecture, contracts, and risks. `spec-tasks` then produces a dependency-ordered `tasks.md` where each task is small enough for a single `workspace.apply_patch` chain.

**Why this priority**: Planning and task breakdown are what make implementation predictable on a 3B model. Large, ambiguous tasks cause the model to exceed its tool-call failure budget; small, scoped tasks succeed.

**Independent Test**: Can be fully tested by running `spec-plan` and `spec-tasks` against a draft spec and verifying that `plan.md` and `tasks.md` exist, that tasks reference the plan, and that task dependencies form a DAG.

**Acceptance Scenarios**:

1. **Given** `specs/my-feature/spec.md` exists, **When** `spec-plan` runs, **Then** it writes `specs/my-feature/plan.md` containing architecture overview, component contracts, and risk assessment sections
2. **Given** `plan.md` exists, **When** `spec-tasks` runs, **Then** it writes `specs/my-feature/tasks.md` with a numbered, dependency-ordered task list
3. **Given** a task in `tasks.md`, **When** inspected, **Then** it includes: task ID, description, target sub-tree, allowed file globs, change budget (max files and lines), and pre-commit gate command
4. **Given** the tasks are complete, **When** validated, **Then** the dependency graph contains no cycles and every task ID is referenced at most once as a dependency

---

### User Story 3 - Gated Implementation with LocalRepoWorkspace (Priority: P2)

After user approval, `spec-implement` walks `tasks.md` one task at a time. For each task it loads the appropriate kit, applies a patch through `workspace.apply_patch`, runs the pre-commit gate, commits on a topic branch, and handles change-budget enforcement.

**Why this priority**: This is where abstract plans become concrete code changes. The integration with `LocalRepoWorkspace` ensures branch hygiene, audit logging, and pre-commit validation.

**Independent Test**: Can be fully tested by running `spec-implement` against a small feature with 2–3 tasks and verifying that commits appear on a topic branch, the pre-commit gate ran, and the workspace journal contains the diff.

**Acceptance Scenarios**:

1. **Given** `tasks.md` exists and the user approved implementation, **When** `spec-implement` starts, **Then** it creates or reuses a topic branch matching the workspace's allowed prefix (e.g., `hermes/my-feature`)
2. **Given** a task targets `web/` files, **When** `spec-implement` runs the pre-commit gate, **Then** it executes the workspace-wide command `npm run lint && npm test`
3. **Given** a task exceeds the per-task change budget (max files or lines), **When** `spec-implement` detects the overflow, **Then** it pauses for re-approval before applying the patch
4. **Given** the pre-commit gate fails, **When** `spec-implement` attempts to commit, **Then** the commit is blocked, the failure is surfaced to the gateway, and the agent asks the user how to proceed

---

### User Story 4 - Consistency Analysis and Background Review (Priority: P2)

Before opening a PR, `spec-analyze` validates cross-artifact consistency across `spec.md`, `plan.md`, and `tasks.md`. `spec-review` then invokes the background reviewer over the diff set and appends findings to the PR description.

**Why this priority**: Catching inconsistencies before implementation saves failed commits. Background review before PR opening is the last quality gate before code is shared.

**Independent Test**: Can be fully tested by introducing a deliberate inconsistency (a task references a non-existent plan section) and verifying that `spec-analyze` flags it, and by checking that `spec-review` produces structured findings.

**Acceptance Scenarios**:

1. **Given** `tasks.md` references a plan section that does not exist in `plan.md`, **When** `spec-analyze` runs, **Then** it emits a warning and pauses the loop for correction
2. **Given** all artifacts are consistent, **When** `spec-analyze` runs, **Then** it emits a success summary and allows the loop to proceed
3. **Given** `spec-review` is triggered, **When** the background reviewer processes the diff, **Then** it writes structured findings (severity, file, line, recommendation) into the workspace journal
4. **Given** findings exist, **When** `workspace.open_pr` runs, **Then** the PR description includes a summary of spec-analyze results and background-reviewer findings

---

### Edge Cases

- What happens when `spec-seed.json` references a target workspace that is not registered in `workspaces.yaml`? `spec-specify` must refuse to write and ask the user to register the workspace or select an alternative target.
- How does the system handle a user who approves implementation but then revokes approval mid-task? The currently active patch is rolled back (via `git checkout -- .` or a stash), the workspace is left clean, and the agent reports the abort.
- What happens when `spec-tasks` produces a cyclic dependency graph? `spec-analyze` must detect the cycle, emit a clear error naming the involved task IDs, and pause for manual correction.
- How does `spec-implement` handle a task whose allowed file globs do not match any files in the workspace? It must emit a warning, skip the task with a note in the commit message, and continue to the next task rather than failing the entire implementation.
- What happens when `spec-implement` encounters a merge conflict during `workspace.apply_patch`? The agent must surface the conflict files to the user, offer to resolve via a follow-up task, and never auto-resolve.
- What happens when the background reviewer is disabled in user config while `spec-review` is invoked? `spec-review` must degrade gracefully to a self-check (diff stats, file count, test command presence) and note the degradation in the PR description.
- How does the bundle handle a spec that spans both `azure-api` and `hermes-lite` repos? Cross-repo plans are disallowed; the agent must suggest splitting into two coordinated specs with linked IDs and separate `spec-seed.json` envelopes.
- What happens when a task's pre-commit gate command is not installed in the workspace? The gate is recorded as `skipped` with a warning; the commit proceeds but the PR description notes the missing gate.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create a new `skills/development/spec-kit/` directory with a manifest entry exposing `/spec` as a slash command
- **FR-002**: `spec-constitution` MUST create or update `<workspace>/specs/constitution.md` with governing principles, tone, and non-negotiables
- **FR-003**: `spec-specify` MUST read `spec-seed.json` from `~/repos/knowledge/seeds/` and produce `<workspace>/specs/<feature>/spec.md`
- **FR-004**: `spec-clarify` MUST generate up to five targeted clarification questions and await user answers in the originating gateway
- **FR-005**: `spec-clarify` MUST write the user's answers back into `spec.md` under a "Clarifications" section
- **FR-006**: `spec-plan` MUST produce `<workspace>/specs/<feature>/plan.md` with architecture, contracts, and risks sections
- **FR-007**: `spec-plan` MUST read the `dev`, `web`, `azure`, `infra`, and `api` memory profiles as needed for context
- **FR-008**: `spec-tasks` MUST produce a dependency-ordered `<workspace>/specs/<feature>/tasks.md` keyed off `plan.md`
- **FR-009**: Each task in `tasks.md` MUST include: task ID, description, target sub-tree, allowed file globs, change budget, and pre-commit gate command
- **FR-010**: `spec-test` MUST optionally emit `<workspace>/specs/<feature>/tests.md` describing executable requirements derived from `spec.md` and `plan.md`
- **FR-011**: `spec-analyze` MUST perform non-destructive cross-artifact consistency analysis across `spec.md`, `plan.md`, and `tasks.md`
- **FR-012**: `spec-checklist` MUST generate a verification checklist for the active feature
- **FR-013**: `spec-implement` MUST execute tasks one-by-one through the `LocalRepoWorkspace` tool set
- **FR-014**: `spec-implement` MUST create or reuse a topic branch matching the workspace's allowed prefix and never mutate `main`/`master` directly
- **FR-015**: `spec-implement` MUST run the configured pre-commit gate before each commit and block the commit on failure
- **FR-016**: `spec-implement` MUST honor the per-workspace change budget; tasks exceeding the budget MUST pause for re-approval
- **FR-017**: `spec-review` MUST invoke the background reviewer over the diff set and surface findings before opening a PR
- **FR-018**: The transition from `arxiv-write` to `spec-specify` MUST be a mandatory user-confirmed approval gate
- **FR-019**: The transition from `spec-tasks` to `spec-implement` MUST be the second mandatory approval gate
- **FR-020**: Cross-repo plans MUST be explicitly disallowed; changes needing multiple repos MUST become two coordinated specs with linked IDs
- **FR-021**: Each skill commit MUST include a spec-kit-aware commit message with: `Spec:`, `Task:`, `Source:`, `Session:`, and `Repo:` fields
- **FR-022**: The bundle MUST bind to the `spec` and `dev` memory profiles so spec artifacts and repo conventions are isolated from other workflows
- **FR-023**: All artifact templates (`spec.md`, `plan.md`, `tasks.md`, etc.) MUST match the shapes produced by the upstream `specify` CLI where the pattern is defined

### Key Entities

- **SpecSeed**: A structured JSON envelope produced by `arxiv-write` and consumed by `spec-specify`. Contains proposed feature title, summary, problem statement, candidate approach, citations, and acceptance criteria draft.
- **SpecKitWorkspace**: The active workspace (`azure-api`, `hermes-lite`, or `knowledge`) against which the spec-kit is running. All file mutations are scoped to this workspace.
- **Constitution**: The `specs/constitution.md` file in a workspace that governs tone, principles, and non-negotiables for the spec process.
- **SpecArtifact**: A family of markdown files (`spec.md`, `plan.md`, `tasks.md`, `analyze.md`, `checklist.md`, `tests.md`) produced and consumed by the spec-kit skills.
- **TaskRecord**: A single entry in `tasks.md` with ID, description, target sub-tree, allowed file globs, change budget, and pre-commit gate.
- **ApprovalGate**: A user-confirmation checkpoint that blocks automatic progression between stages of the spec-kit pipeline. Two gates are mandatory: research→spec and tasks→implement.
- **BackgroundReviewer**: A deferred-queue process that audits the diff set produced by `spec-implement` and emits structured findings before the PR is opened.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `spec-specify` produces a `spec.md` that passes the spec template schema validation in at least 95% of cases
- **SC-002**: `spec-plan` produces a `plan.md` within 120 seconds for features scoped to a single sub-tree (e.g., `web/` or `agent/`)
- **SC-003**: `spec-tasks` produces a `tasks.md` with no cyclic dependencies and every task referencing an existing plan section
- **SC-004**: `spec-implement` successfully commits at least one task per minute on average for tasks under the change budget
- **SC-005**: The pre-commit gate blocks at least one commit in integration testing when a deliberate lint error is introduced
- **SC-006**: The background reviewer produces findings within 60 seconds per 10 files changed
- **SC-007**: A complete spec→plan→tasks→implement cycle for a 3-task feature completes end-to-end in under 15 minutes on the Jetson 25 W power mode
- **SC-008**: The agent never mutates `main`/`master` directly; every commit lands on a topic branch, verified by git log inspection

## Assumptions

- `LocalRepoWorkspace` (§5.9) is available and the target workspace is registered in `~/.hermes-lite/workspaces.yaml`
- The upstream `specify` CLI behavior is the reference implementation where the spec-kit pattern is ambiguous
- The knowledge repo (`~/repos/knowledge`) contains `spec-seed.json` envelopes that conform to the expected schema
- Each workspace has a `specs/` directory and a `specs/constitution.md` file (created by `spec-constitution` if missing)
- The `spec` and `dev` memory profiles are available and contain relevant conventions for the target workspace
- Pre-commit gate commands are installed and configured per workspace (e.g., `pre-commit`, `npm run lint`, `pytest -q`, `cargo check`)
- The user is available in the originating gateway to answer clarification questions and approve gates; unattended auto-promotion is never allowed
- A feature scoped to `azure-api` may span `infra/`, `web/`, and `api/` within that single repo, but may not also modify `hermes-lite` source in the same spec
- The background reviewer queue is configured in deferred mode (`curator.mode: deferred_queue`) and reachable from the spec-kit context
