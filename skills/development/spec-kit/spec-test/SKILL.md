---
name: spec-test
description: "Optionally emit tests.md describing executable requirements derived from spec and plan."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [spec-kit, testing, tdd, verification]
    related_skills: [spec-plan, spec-implement]
---

# spec-test

## Title
 spec-test — Test Requirements Authoring

## Description
Read `spec.md` and `plan.md` and optionally emit `<workspace>/specs/<feature>/tests.md` describing executable requirements. This is a TDD-style step that can be skipped if the user does not request tests. The output serves as acceptance criteria for the implementation phase.

## Trigger Conditions
- User invokes `/spec test`
- User requests test-driven development during `/spec` workflow

## Inputs
- `<workspace>/specs/<feature>/spec.md`
- `<workspace>/specs/<feature>/plan.md`

## Outputs
- `<workspace>/specs/<feature>/tests.md` (optional)

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the spec-kit bundle.
