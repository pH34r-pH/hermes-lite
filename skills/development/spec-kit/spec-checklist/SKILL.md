---
name: spec-checklist
description: "Generate a verification checklist for the active feature."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [spec-kit, checklist, verification, qa]
    related_skills: [spec-test, spec-implement]
---

# spec-checklist

## Title
 spec-checklist — Verification Checklist Generation

## Description
Generate `<workspace>/specs/<feature>/checklist.md` for the active feature. The checklist includes acceptance criteria derived from `spec.md`, implementation checkpoints from `plan.md`, and per-task verification steps from `tasks.md`. It is used during and after `spec-implement` to ensure nothing is missed.

## Trigger Conditions
- User invokes `/spec checklist`
- `spec-test` or `spec-analyze` completes and the user requests a checklist

## Inputs
- `<workspace>/specs/<feature>/spec.md`
- `<workspace>/specs/<feature>/plan.md`
- `<workspace>/specs/<feature>/tasks.md`

## Outputs
- `<workspace>/specs/<feature>/checklist.md`

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the spec-kit bundle.
