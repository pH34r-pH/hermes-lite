# Implementation Plan: LocalRepoWorkspace Plugin

**Branch**: `010-local-repo-workspace` | **Date**: 2026-05-24 | **Spec**: `specs/010-local-repo-workspace/spec.md`

**Input**: Feature specification from `/specs/010-local-repo-workspace/spec.md`

## Summary

Ship a `plugins/local_repo_workspace/` plugin that is the only sanctioned path for the agent to mutate code outside `~/.hermes-lite/`. The plugin maintains a workspace registry at `~/.hermes-lite/workspaces.yaml` enumerating every repo hermes may touch. It exposes typed tools (`workspace.list`, `workspace.locate`, `workspace.status`, `workspace.diff`, `workspace.apply_patch`, `workspace.commit`, `workspace.push`, `workspace.open_pr`) that the agent loop can call. Each tool is schema-validated and respects registry constraints.

Branch hygiene is enforced identically to micromanager: default and protected branches (`main`, `master`) are never mutated directly; topic branches matching the allowed prefix are created or reused. A per-directive change budget (max N files, max M lines) blocks overage without a second confirmation envelope. A pre-commit gate runs per workspace before each commit and blocks on failure. A structured change journal is written under `~/.hermes-lite/journal/<session-id>/<step>.json` containing the unified diff, commit metadata, and test output. Git operations use subprocess with environment scrubbing, SSH agent socket pinned per workspace, and working-copy-only `git config` overrides.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: `pyyaml` (workspace registry parsing), `git` (system dependency), existing `agent/tool_guardrails.py`, existing `agent/file_safety.py`, existing `plugins/kanban/` (worktree isolation delegation), existing `agent/redact.py`

**Storage**: `~/.hermes-lite/workspaces.yaml` (workspace registry), `~/.hermes-lite/journal/<session-id>/<step>.json` (change journal), workspace git repositories on local disk

**Testing**: pytest, plus integration tests requiring real git repos and GitHub CLI / API credentials

**Target Platform**: Linux (Jetson Orin Nano) for agent; local git repos for target workspaces

**Project Type**: Plugin with typed tool surface, YAML registry, JSON journal, and git subprocess orchestration

**Performance Goals**: `workspace.locate` resolves by name in under 1 second; `workspace.apply_patch` applies a small patch and runs pre-commit gate within 30 seconds; complete edit-commit-push-PR cycle for a 1-file change completes in under 2 minutes

**Constraints**: Default and protected branches are never mutated directly; force-push and history-rewrite are disabled; path-traversal and symlink-escape attempts are rejected; unregistered repos are read-only; budget overage always requires re-approval regardless of `approval_mode`

**Scale/Scope**: One plugin directory (~8 typed tools, ~800-1000 LOC of Python support modules), YAML registry schema, JSON journal schema, integration with skill loading and tool registry

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Security-First Development**: Unregistered repos are read-only; path traversal and symlink escapes are rejected; force-push is disabled; environment scrubbing on git subprocess prevents credential leakage.
- **Defense in Depth**: Branch hygiene enforced at the plugin layer (topic branches only); pre-commit gate blocks commits; change budget blocks overage; `agent/tool_guardrails.py` and `agent/file_safety.py` remain as lowest-level safety net.
- **Secure Defaults**: Default `approval_mode` for new workspaces is `pr-only`; `main`/`master` mutation is prohibited; unregistered repos refuse writes.
- **Dependency Management**: `git` and `gh` (optional) are system dependencies; no heavy git SDK packages added to the Python environment.

**Result**: PASS — design aligns with all constitution principles.

## Project Structure

### Documentation (this feature)

```text
specs/010-local-repo-workspace/
├── plan.md              # This file
├── spec.md              # Feature specification
└── tasks.md             # Concrete task list
```

### Source Code (repository root)

```text
plugins/local_repo_workspace/
├── __init__.py                     # Plugin entry point and tool registration
├── plugin.py                       # Plugin lifecycle + config loader
├── registry.py                     # WorkspaceRegistry YAML read/write/validate
├── models.py                       # WorkspaceEntry, ChangeBudget, TopicBranch dataclasses
├── tools/
│   ├── __init__.py
│   ├── list_workspaces.py          # workspace.list tool
│   ├── locate_workspace.py         # workspace.locate tool
│   ├── workspace_status.py         # workspace.status tool
│   ├── workspace_diff.py           # workspace.diff tool
│   ├── apply_patch.py              # workspace.apply_patch tool
│   ├── commit.py                   # workspace.commit tool
│   ├── push.py                     # workspace.push tool
│   └── open_pr.py                  # workspace.open_pr tool
├── lib/
│   ├── __init__.py
│   ├── git_runner.py               # Subprocess git wrapper with env scrubbing + SSH socket pinning
│   ├── branch_hygiene.py           # Topic-branch creation / reuse; main/master protection
│   ├── change_budget.py            # Per-directive file/line counter + re-approval gate
│   ├── precommit_gate.py           # Gate command runner + result capture
│   ├── change_journal.py           # JSON journal writer under ~/.hermes-lite/journal/
│   └── path_guard.py               # Path traversal + symlink escape detection
├── schemas/
│   ├── workspace_registry.schema.yaml   # workspaces.yaml schema
│   └── change_journal.schema.json       # journal entry JSON schema

~/.hermes-lite/workspaces.yaml      # Workspace registry (user-managed)
~/.hermes-lite/journal/<session-id>/   # Change journal directory

agent/
└── tool_surface.py                 # UPDATE — register workspace.* typed tools in allowlist
```

**Structure Decision**: Single plugin directory because all typed tools share the same registry, the same git runner, and the same journal. Splitting into multiple plugins would duplicate registry locking and git environment setup logic. The `tools/` subdirectory keeps each typed tool in its own file for clarity, while `lib/` holds shared infrastructure.

## Complexity Tracking

> No constitution violations. The feature is a single plugin with a bounded tool surface (~8 tools), which aligns with the tool-surface slimming goal (spec 003). All mutable operations are gated by registry constraints, branch hygiene, change budgets, and pre-commit checks.
