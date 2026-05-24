---
name: spec-clarify
description: "Generate up to five targeted clarification questions and record user answers back into spec.md."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [spec-kit, clarification, interactive, requirements]
    related_skills: [spec-specify, spec-plan]
---

# spec-clarify

## Title
 spec-clarify — Specification Clarification

## Description
Read the draft `spec.md` and generate up to five targeted clarification questions. Await the user's answers in the originating gateway, then write the answers back into `spec.md` under a "Clarifications" section. This reduces ambiguity before planning begins.

## Trigger Conditions
- User invokes `/spec clarify`
- `spec-specify` detects underspecified requirements
- User adds `[NEEDS CLARIFICATION]` tags in `spec.md`

## Inputs
- Draft `<workspace>/specs/<feature>/spec.md`
- User answers (provided interactively in the gateway)

## Outputs
- Updated `<workspace>/specs/<feature>/spec.md` with Clarifications section

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the spec-kit bundle.
