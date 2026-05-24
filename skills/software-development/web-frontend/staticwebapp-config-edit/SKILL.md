---
name: staticwebapp-config-edit
description: "Safely edit staticwebapp.config.json while preserving schema validity."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [swa, static-web-app, config, edit, mutation]
    related_skills: [staticwebapp-config-validate]
---

# staticwebapp-config-edit

## Title
 staticwebapp-config-edit — SWA Config Safe Editing

## Description
Safely edit `staticwebapp.config.json` while preserving schema validity. Uses round-trip JSON parsing and re-validation after every change. Can add routes, headers, rewrites, or redirects as requested. Gated by explicit user confirmation before writing.

## Trigger Conditions
- User invokes `/web config-edit`
- User asks to add, remove, or modify SWA routes, headers, or rewrites

## Inputs
- Desired config changes (route, method, rewrite, redirect, headers)
- `staticwebapp.config.json` file path

## Outputs
- Updated config file (on approval)
- Validation result confirming schema validity

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the web-frontend bundle.
