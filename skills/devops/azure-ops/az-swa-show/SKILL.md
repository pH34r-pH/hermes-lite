---
name: az-swa-show
description: "Return current Azure Static Web App configuration."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [azure, swa, static-web-app, read-only]
    related_skills: [az-resource-list, az-swa-deploy]
---

# az-swa-show

## Title
 az-swa-show — Static Web App Configuration Inspection

## Description
Return the current Azure Static Web App configuration including name, default hostname, custom domains, and current routing rules. Handle SWA not found gracefully.

## Trigger Conditions
- User invokes `/azure swa show`
- User asks for SWA configuration, hostname, or routing rules

## Inputs
- SWA name from `azure` memory profile

## Outputs
- SWA name, default hostname, custom domains, routing rules

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the azure-ops bundle.
