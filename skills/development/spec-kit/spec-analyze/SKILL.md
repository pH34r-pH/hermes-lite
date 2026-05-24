---
name: spec-analyze
description: "Non-destructive cross-artifact consistency analysis across spec.md, plan.md, and tasks.md."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [spec-kit, analysis, validation, consistency]
    related_skills: [spec-tasks, spec-review]
---

# spec-analyze

## Title
 spec-analyze — Cross-Artifact Consistency Analysis

## Description
Read `spec.md`, `plan.md`, and `tasks.md` and perform non-destructive validation. Checks include: every task ID is unique, every dependency exists, no cycles in the dependency graph, and every task references an existing plan section. On failure, emits warnings and pauses the loop for correction. On success, emits a success summary and allows the loop to proceed.

## Trigger Conditions
- User invokes `/spec analyze`
- `spec-tasks` completes and the user requests validation before implementation

## Inputs
- `<workspace>/specs/<feature>/spec.md`
- `<workspace>/specs/<feature>/plan.md`
- `<workspace>/specs/<feature>/tasks.md`

## Outputs
- Consistency report (emitted in conversation; artifacts are not mutated)
- `<workspace>/specs/<feature>/analyze.md` (optional, for audit trail)

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the spec-kit bundle.
