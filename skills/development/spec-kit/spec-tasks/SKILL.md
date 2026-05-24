---
name: spec-tasks
description: "Produce a dependency-ordered tasks.md keyed off plan.md sections."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [spec-kit, task-breakdown, planning, dependencies]
    related_skills: [spec-plan, spec-implement, spec-analyze]
---

# spec-tasks

## Title
 spec-tasks — Task Breakdown and Ordering

## Description
Read `plan.md` and produce `<workspace>/specs/<feature>/tasks.md`. Each task is small enough for a single `workspace.apply_patch` chain. Tasks include: task ID, description, target sub-tree, allowed file globs, change budget (max files and lines), and pre-commit gate command. The dependency graph is validated for cycles before writing.

## Trigger Conditions
- User invokes `/spec tasks`
- `spec-plan` completes and the user confirms readiness to break down work

## Inputs
- `<workspace>/specs/<feature>/plan.md`
- Workspace conventions (from memory profiles)

## Outputs
- `<workspace>/specs/<feature>/tasks.md`

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the spec-kit bundle.
