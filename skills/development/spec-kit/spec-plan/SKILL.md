---
name: spec-plan
description: "Produce plan.md with architecture overview, component contracts, and risk assessment."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [spec-kit, planning, architecture, design]
    related_skills: [spec-specify, spec-tasks]
    memory_profiles: [dev, web, azure, infra, api]
---

# spec-plan

## Title
 spec-plan — Architecture and Implementation Planning

## Description
Read `spec.md` and produce `<workspace>/specs/<feature>/plan.md`. The plan includes architecture overview, component contracts, risk assessment, and project structure. It reads the `dev`, `web`, `azure`, `infra`, and `api` memory profiles as needed for workspace-specific context. Cross-repo plans are explicitly disallowed.

## Trigger Conditions
- User invokes `/spec plan`
- `spec-clarify` completes and the user confirms readiness to plan

## Inputs
- `<workspace>/specs/<feature>/spec.md`
- Workspace memory profiles (`dev`, `web`, `azure`, `infra`, `api`)
- `spec-constitution` tone/principles

## Outputs
- `<workspace>/specs/<feature>/plan.md`

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the spec-kit bundle.
