# Feature Specification: LocalRepoWorkspace Plugin

**Feature Branch**: `010-local-repo-workspace`

**Created**: 2026-05-24

**Status**: Draft

**Input**: User description: "New plugin under plugins/local_repo_workspace/. Workspace registry at ~/.hermes-lite/workspaces.yaml. Typed tools: workspace.list, .locate, .status, .diff, .apply_patch, .commit, .push, .open_pr. Branch hygiene (never mutate main). Change budget, pre-commit gate, structured change journal. Read REDESIGN.md §5.9, §9."

## Current State

Upstream Hermes Agent has built-in file read/write tools and shell execution through `tools/` and `toolsets.py`, plus `software-development/` and `devops/` skills for git operations. However, there is **no centralized, registry-bounded workspace mediator** for local repo mutations. The agent can edit files anywhere the process has permissions, with only generic `agent/tool_guardrails.py` and `agent/file_safety.py` for protection. There is no workspace registry enumerating approved repos, no typed tool surface scoped to a repo, no branch-hygiene enforcement (the agent can in theory commit directly to `main`), no change-budget tracking, no pre-commit gate integration, and no structured change journal. The upstream `plugins/kanban/` plugin demonstrates worktree-based branch routing but does not provide a general workspace abstraction for arbitrary repos. There is no concept of `approval_mode` per workspace (`auto`, `confirm`, `pr-only`, `read-only`).

## Target State

Hermes-lite ships a `plugins/local_repo_workspace/` plugin that is the **only sanctioned path** for the agent to mutate code outside `~/.hermes-lite/`. The plugin maintains a workspace registry at `~/.hermes-lite/workspaces.yaml` enumerating every repo hermes may touch, with fields: id, friendly name, absolute path, default branch, allowed branch prefixes, push remote, commit author identity, allowed file globs, required reviewers, and `approval_mode`. The plugin exposes typed tools (`workspace.list`, `workspace.locate`, `workspace.status`, `workspace.diff`, `workspace.apply_patch`, `workspace.commit`, `workspace.push`, `workspace.open_pr`) that the agent loop can call. Each tool is schema-validated and respects registry constraints.

Branch hygiene is enforced identically to micromanager: default and protected branches (`main`, `master`) are never mutated directly; topic branches matching the allowed prefix (e.g., `hermes/`, `bot/`) are created or reused. A per-directive change budget (max N files, max M lines) blocks overage without a second confirmation envelope. A pre-commit gate runs per workspace before each commit and blocks on failure. A structured change journal is written under `~/.hermes-lite/journal/<session-id>/<step>.json` containing the unified diff, commit metadata, and test output. Git operations use subprocess with environment scrubbing, SSH agent socket pinned per workspace, and working-copy-only `git config` overrides.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Register and List Workspaces (Priority: P1)

A user adds a new local repo to the workspace registry via the TUI or a command, then queries the registry to see all registered workspaces. `workspace.list` returns the registry contents; `workspace.locate` resolves a natural-language target to a registered workspace.

**Why this priority**: The registry is the foundation of all bounded repo access. Without it, the agent cannot safely resolve which repo a directive targets.

**Independent Test**: Can be fully tested by adding a workspace to the registry and running `workspace.list` and `workspace.locate` against it.

**Acceptance Scenarios**:

1. **Given** the user registers `~/repos/my-blog` as workspace `my-blog`, **When** `workspace.list` runs, **Then** it returns an entry with id `my-blog`, path `~/repos/my-blog`, default branch `main`, and allowed prefix `hermes/`
2. **Given** the user asks "update the website repo", **When** `workspace.locate` runs, **Then** it resolves to the workspace whose friendly name or git URL best matches, and returns the absolute path and metadata
3. **Given** two workspaces have similar names, **When** `workspace.locate` runs with ambiguous input, **Then** it returns a clarification request to the user rather than guessing
4. **Given** a path under `~/repos/` is not in the registry, **When** the agent attempts to write to it, **Then** the tool refuses and instructs the user to register the workspace first

---

### User Story 2 - Apply a Patch with Pre-Commit Gate and Change Budget (Priority: P1)

A user asks hermes-lite to edit a file in a registered workspace. `workspace.apply_patch` validates the patch applies cleanly, enforces the change budget, runs the pre-commit gate, and prepares a commit. If the budget is exceeded, it pauses for re-approval.

**Why this priority**: This is the core write path. Bounded patches, pre-commit validation, and budget enforcement prevent unreviewed, broken, or excessive changes.

**Independent Test**: Can be fully tested by generating a small patch against a registered workspace, running `workspace.apply_patch`, and verifying the staging area, gate result, and journal entry.

**Acceptance Scenarios**:

1. **Given** a workspace has change budget `max_files: 2, max_lines: 30`, **When** a patch touches 1 file and 5 lines, **Then** it applies cleanly, the pre-commit gate runs, and the journal records the diff
2. **Given** a patch touches 5 files, **When** `workspace.apply_patch` runs, **Then** it pauses and asks the user for re-approval before applying
3. **Given** the pre-commit gate command is `npm run lint && npm test`, **When** the gate fails, **Then** the commit is blocked, the failure output is surfaced to the gateway, and the agent asks the user how to proceed
4. **Given** the patch includes a file outside the workspace's allowed globs, **When** `workspace.apply_patch` runs, **Then** it rejects the hunk and surfaces the rejection reason

---

### User Story 3 - Commit, Push, and Open a PR with Branch Hygiene (Priority: P2)

After a patch is staged and approved, `workspace.commit` writes a schema-validated commit message on a topic branch. `workspace.push` pushes to the registered remote. `workspace.open_pr` opens a PR with a body linking back to the originating gateway message.

**Why this priority**: This closes the loop from gateway directive to shared code change. Branch hygiene ensures `main` is never mutated directly; PR linkage preserves audit trail.

**Independent Test**: Can be fully tested by running the full commit-push-PR chain against a test repo and verifying the branch name, commit message schema, remote URL, and PR body.

**Acceptance Scenarios**:

1. **Given** the workspace default branch is `main` and allowed prefix is `hermes/`, **When** `workspace.commit` runs, **Then** it creates or reuses `hermes/<topic>` off `main` and never commits to `main` directly
2. **Given** the workspace remote is `git@github.com:owner/repo.git`, **When** `workspace.push` runs, **Then** it pushes the topic branch to that remote using the workspace-pinned SSH agent socket
3. **Given** the originating gateway is Discord channel `#general`, **When** `workspace.open_pr` runs, **Then** the PR description includes a link to the Discord message, the diff summary, and the session ID
4. **Given** the workspace `approval_mode` is `pr-only`, **When** implement completes, **Then** a PR is opened and the agent reports the PR URL to the gateway

---

### User Story 4 - Structured Change Journal and Audit Replay (Priority: P2)

Every mutation produces a structured change journal entry under `~/.hermes-lite/journal/<session-id>/`. The curator and background reviewer can read the journal to audit changes. A user can query the journal to see what was changed in a session.

**Why this priority**: Auditability is a core security requirement. The journal is the canonical record of what the agent did, when, and why.

**Independent Test**: Can be fully tested by running a workspace write sequence and inspecting the journal directory for the expected JSON files.

**Acceptance Scenarios**:

1. **Given** a session makes two commits, **When** the journal is inspected, **Then** `~/.hermes-lite/journal/<session-id>/1.json` and `2.json` exist, each containing the unified diff, commit SHA, pre-commit gate result, and timestamp
2. **Given** a patch fails to apply, **When** `workspace.apply_patch` rejects it, **Then** the journal records the rejection with the rejected hunks and the reason
3. **Given** the background reviewer reads the journal, **When** it processes the diff set, **Then** it produces findings referencing the exact journal step numbers and file paths
4. **Given** the user asks "what did you change in session abc123?", **When** the agent queries the journal, **Then** it returns a summary of files touched, lines changed, and PR links

---

### Edge Cases

- What happens when `workspaces.yaml` is malformed or missing? The plugin must refuse all workspace operations and emit a clear error with the path to a template file.
- How does the system handle a workspace whose git working tree is dirty before the agent starts? `workspace.status` must report the dirty state; `workspace.apply_patch` must refuse to apply until the tree is clean or the user approves a stash.
- What happens when `workspace.push` receives a non-fast-forward rejection? The plugin must attempt `git pull --rebase`, replay the commit, and surface the result. If conflicts exist, it must stop and ask for direction.
- How does the plugin handle a pre-commit gate command that is not installed? The gate is recorded as `skipped` with a warning; the commit proceeds but the PR description notes the missing gate.
- What happens when the SSH agent socket is missing for a workspace? `workspace.push` must emit a clear error identifying the socket path and suggest how to start the agent.
- How does the plugin handle a `workspace.open_pr` when the GitHub CLI is not installed? It must gracefully fall back to the GitHub REST API via `requests`, or emit instructions for manual PR creation.
- What happens when a user overrides `approval_mode` to `auto` but the change exceeds the budget? The budget overage ALWAYS requires re-approval, regardless of `approval_mode`.
- How does worktree isolation interact with `LocalRepoWorkspace`? When the kanban plugin creates a worktree, `LocalRepoWorkspace` delegates file operations to the worktree path while still enforcing the same registry constraints.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The plugin MUST maintain a workspace registry at `~/.hermes-lite/workspaces.yaml` with fields: id, friendly_name, path, default_branch, allowed_branch_prefixes, push_remote, commit_author, allowed_file_globs, required_reviewers, approval_mode
- **FR-002**: `workspace.list` MUST return all registered workspaces with their metadata
- **FR-003**: `workspace.locate` MUST resolve a natural-language target to a registered workspace by matching friendly_name, git remote URL, and path basename; ambiguous matches MUST ask for clarification
- **FR-004**: `workspace.status` MUST report the current branch, dirty state, and ahead/behind counts for the workspace
- **FR-005**: `workspace.diff` MUST return the unified diff of the working tree or a specified commit range, scoped to allowed file globs
- **FR-006**: `workspace.apply_patch` MUST validate that the patch applies cleanly, enforce allowed file globs, and stage the result
- **FR-007**: `workspace.apply_patch` MUST enforce the per-workspace change budget (max files and max lines); overage MUST pause for re-approval
- **FR-008**: `workspace.commit` MUST create or reuse a topic branch matching the allowed prefix and NEVER mutate `main`/`master` directly
- **FR-009**: `workspace.commit` MUST write a schema-validated commit message including: summary line, optional body, `Source:`, `Session:`, and `Author-Identity:` fields
- **FR-010**: `workspace.push` MUST push the topic branch to the registered remote using the workspace-pinned SSH agent socket
- **FR-011**: `workspace.push` MUST verify the remote URL matches the registry before pushing
- **FR-012**: `workspace.open_pr` MUST open a PR using the GitHub CLI or REST API, with a body linking to the originating gateway message and including diff statistics
- **FR-013**: The plugin MUST run a pre-commit gate per workspace before each commit; a failed gate MUST block the commit
- **FR-014**: The plugin MUST write a structured change journal under `~/.hermes-lite/journal/<session-id>/<step>.json` containing: diff, commit metadata, pre-commit gate result, and timestamp
- **FR-015**: Git subprocesses MUST execute with environment scrubbing (no inherited `GIT_*` overrides), workspace-pinned SSH agent socket, and working-copy-only `git config` overrides
- **FR-016**: Path traversal attempts MUST be rejected by resolving all inputs against the workspace root and checking for symlink escapes
- **FR-017**: Force-push and history-rewrite operations MUST be disabled; `workspace.push` MUST never pass `--force`
- **FR-018**: The plugin MUST support four `approval_mode` values: `auto` (small changes commit without asking), `confirm` (every change waits for approval), `pr-only` (commit and push to topic branches but never merge), `read-only` (no writes)
- **FR-019**: The default `approval_mode` for new workspaces MUST be `pr-only`
- **FR-020**: The plugin MUST delegate to the kanban plugin's worktree behavior when a directive requests an isolated change set
- **FR-021**: Unregistered repos MUST be read-only; the plugin MUST refuse writes and instruct the user to register the workspace

### Key Entities

- **WorkspaceRegistry**: The `~/.hermes-lite/workspaces.yaml` file enumerating all repos hermes may touch.
- **WorkspaceEntry**: A single registry entry with id, friendly_name, path, default_branch, allowed_branch_prefixes, push_remote, commit_author, allowed_file_globs, required_reviewers, and approval_mode.
- **ChangeBudget**: The per-directive limits (max files, max lines) enforced by `workspace.apply_patch`.
- **PreCommitGate**: A workspace-configured command (e.g., `pre-commit run --all-files`, `npm run lint && npm test`) that must pass before a commit is allowed.
- **ChangeJournal**: A structured JSON file under `~/.hermes-lite/journal/<session-id>/<step>.json` recording diffs, metadata, and gate results.
- **TopicBranch**: A branch created off the default branch with a prefix from the workspace registry (e.g., `hermes/update-hero-copy`).
- **SshAgentSocket**: The per-workspace SSH agent socket used for authenticated git push operations.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `workspace.locate` resolves a registered workspace by name in under 1 second
- **SC-002**: `workspace.apply_patch` applies a valid patch and runs the pre-commit gate within 30 seconds for a small change (≤2 files, ≤30 lines)
- **SC-003**: The change budget blocks at least one over-budget change in integration testing
- **SC-004**: The pre-commit gate blocks at least one commit when a deliberate lint error is introduced
- **SC-005**: `workspace.commit` never mutates `main`/`master` directly in integration testing; every commit lands on a topic branch
- **SC-006**: `workspace.push` verifies the remote URL matches the registry before pushing; a mismatch is refused
- **SC-007**: `workspace.open_pr` produces a PR with a body containing the originating gateway link within 10 seconds
- **SC-008**: The change journal contains an entry for every workspace mutation step, verified by directory listing after a test session
- **SC-009**: A complete edit-commit-push-PR cycle for a 1-file change completes end-to-end in under 2 minutes
- **SC-010**: Path-traversal and symlink-escape attempts are rejected in integration testing

## Assumptions

- The target repo is already cloned on the cyberdeck at the path declared in the registry
- Git is installed and the user has configured SSH keys for the registered remotes
- The GitHub CLI (`gh`) or REST API credentials are available if `workspace.open_pr` is used
- Pre-commit gate commands are installed and configured per workspace
- The kanban plugin is available for worktree-based parallel work isolation
- `agent/tool_guardrails.py` and `agent/file_safety.py` provide the lowest-level safety net; `LocalRepoWorkspace` adds registry-bounded scoping on top
- Workspace paths are under `~/repos/` per the design premise; paths outside this directory may be registered but are subject to additional confirmation
- The user is available in the originating gateway to answer clarification questions and approve gates
- Approval mode `auto` requires explicit opt-in and a tighter change budget than the default
- Commit author identity is configured per workspace; fall back to global git config if absent
