---
name: bicep-deploy
description: "Deploy Bicep modules for the paired SWA + VM topology."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [azure, bicep, deploy, infrastructure-as-code]
    related_skills: [bicep-validate]
---

# bicep-deploy

## Title
 bicep-deploy — Bicep Module Deployment

## Description
Deploy Bicep modules for the paired SWA + VM topology using `az deployment group create` with what-if support. Gated with explicit user confirmation before creating or updating resources.

## Trigger Conditions
- User invokes `/azure bicep deploy`
- User asks to deploy Bicep infrastructure

## Inputs
- Bicep parameter file and template
- Resource group from `azure` memory profile

## Outputs
- Deployment result: success, failure, or what-if preview

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the azure-ops bundle.
