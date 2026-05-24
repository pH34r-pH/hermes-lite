---
name: staticwebapp-config-validate
description: "Validate staticwebapp.config.json against the SWA schema and report errors with JSON paths."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [swa, static-web-app, config, validation, schema]
    related_skills: [staticwebapp-config-edit]
---

# staticwebapp-config-validate

## Title
 staticwebapp-config-validate — SWA Config Schema Validation

## Description
Validate `staticwebapp.config.json` against the SWA schema (`schemas/staticwebapp.config.schema.json`). Emit errors with the exact JSON path and expected type. Detect missing rewrite or redirect target files in the build output. Must reject a malformed config within 2 seconds.

## Trigger Conditions
- User invokes `/web validate`
- User asks to check or validate SWA config

## Inputs
- `staticwebapp.config.json` file path (default `web/staticwebapp.config.json`)
- Build output directory for file-existence checks

## Outputs
- Validation result: pass or error list with JSON path and expected type

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the web-frontend bundle.
