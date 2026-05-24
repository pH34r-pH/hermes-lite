---
name: az-swa-config-update
description: "Edit SWA configuration (routes, auth providers, custom domains) through the Azure API."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [azure, swa, static-web-app, mutation]
    related_skills: [az-swa-show, az-swa-deploy]
---

# az-swa-config-update

## Title
 az-swa-config-update — Static Web App Configuration Update

## Description
Edit SWA configuration including routes, auth providers, and custom domains through the Azure API. All mutations are gated with explicit user confirmation. Uses `AzCliWrapper` to call `az staticwebapp appsettings set` or equivalent.

## Trigger Conditions
- User invokes `/azure swa config-update`
- User asks to add, remove, or modify SWA routes, auth, or domains

## Inputs
- Desired configuration changes
- SWA name from `azure` memory profile

## Outputs
- Updated SWA configuration confirmation

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the azure-ops bundle.
