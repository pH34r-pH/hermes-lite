---
name: bicep-validate
description: "Validate Bicep modules against the Azure schema and report errors."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [azure, bicep, validate, infrastructure-as-code]
    related_skills: [bicep-deploy]
---

# bicep-validate

## Title
 bicep-validate — Bicep Module Validation

## Description
Validate Bicep modules against the Azure schema via `BicepHelper` (wrapping `az bicep build` or `bicep build`). Report errors with file path and line number. Must catch at least one schema error in a deliberately malformed Bicep file during integration testing.

## Trigger Conditions
- User invokes `/azure bicep validate`
- User asks to validate Bicep files

## Inputs
- Bicep file paths or `infra/` directory

## Outputs
- Validation results: pass or error list with file path and line number

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the azure-ops bundle.
