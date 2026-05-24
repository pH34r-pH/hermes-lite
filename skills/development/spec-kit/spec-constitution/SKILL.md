---
name: spec-constitution
description: "Create or update the workspace's specs/constitution.md with governing principles, tone, and non-negotiables."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [spec-kit, constitution, governance, planning]
    related_skills: [spec-specify, spec-plan]
---

# spec-constitution

## Title
 spec-constitution — Workspace Constitution Authoring

## Description
Create or update `<workspace>/specs/constitution.md`. This document governs tone, principles, and non-negotiables for all subsequent spec-kit work in the workspace. If the file is missing, generate it from the constitution template. If it exists, update it with any new principles or constraints discovered during the current session.

## Trigger Conditions
- User invokes `/spec constitution`
- Workspace `specs/constitution.md` is missing before running `spec-specify`
- User explicitly requests to change workspace governance rules

## Inputs
- Target workspace identifier (resolved via `workspace_resolver.py`)
- Optional user-provided principles or tone guidelines
- Existing `specs/constitution.md` if present

## Outputs
- `<workspace>/specs/constitution.md` (created or updated)

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the spec-kit bundle.
