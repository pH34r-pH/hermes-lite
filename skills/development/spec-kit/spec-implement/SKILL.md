---
name: spec-implement
description: "Execute tasks one-by-one through LocalRepoWorkspace; commit on topic branch with pre-commit gates."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [spec-kit, implementation, workspace, git]
    related_skills: [spec-tasks, spec-checklist, spec-review]
    approval_gate: tasks-to-implement
---

# spec-implement

## Title
 spec-implement — Gated Task Execution

## Description
Read `tasks.md` and walk tasks one at a time. For each task: load the appropriate kit, apply a patch via `workspace.apply_patch`, run the pre-commit gate, commit on a topic branch, and handle change-budget enforcement. Never mutates `main`/`master` directly. On pre-commit gate failure, blocks the commit and surfaces the error. On user mid-task abort, rolls back the active patch and leaves the workspace clean.

## Trigger Conditions
- User invokes `/spec implement`
- `spec-tasks` completes and the user approves the tasks-to-implement gate

## Inputs
- `<workspace>/specs/<feature>/tasks.md`
- Workspace configuration (branch prefixes, change budget, pre-commit gate command)

## Outputs
- Commits on topic branch (e.g., `hermes/<feature>`)
- Workspace journal entries for each applied patch
- Updated task status in `tasks.md`

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the spec-kit bundle.
