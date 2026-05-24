---
name: spec-specify
description: "Turn a research outcome or free-form ask into a feature spec (specs/<feature>/spec.md)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [spec-kit, specification, seed-parser]
    related_skills: [spec-constitution, spec-clarify, spec-plan]
---

# spec-specify

## Title
 spec-specify — Feature Specification Authoring

## Description
Read `spec-seed.json` from `~/repos/knowledge/seeds/` (or accept a free-form user ask) and produce `<workspace>/specs/<feature>/spec.md`. This is the bridge between inbound research and outbound engineering work. All seed fields are mapped into the spec template.

## Trigger Conditions
- User invokes `/spec specify <feature-name>`
- `arxiv-write` promotes a `spec-seed.json` and the user confirms the approval gate
- User provides a free-form feature description after `/spec`

## Inputs
- `spec-seed.json` path or raw user feature description
- Target workspace identifier (resolved via `workspace_resolver.py`)
- `spec-constitution` output (tone/principles)

## Outputs
- `<workspace>/specs/<feature>/spec.md`

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the spec-kit bundle.
