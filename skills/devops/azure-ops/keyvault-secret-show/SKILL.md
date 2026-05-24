---
name: keyvault-secret-show
description: "Resolve secrets read-only from Azure Key Vault; writes always require confirmation."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [azure, keyvault, secrets, read-only]
    related_skills: [apikey-rotate]
---

# keyvault-secret-show

## Title
 keyvault-secret-show — Key Vault Secret Resolution

## Description
Resolve secrets read-only from Azure Key Vault. Never log secret values; redact in output and logs. Writes (create/update secrets) always require confirmation mode. Used by `apikey-rotate` to read current secrets before rotation.

## Trigger Conditions
- User invokes `/azure keyvault show <secret-name>`
- User asks to read a secret from Key Vault

## Inputs
- Secret name
- Key Vault name from `azure` memory profile

## Outputs
- Secret metadata (name, version, enabled status); value is redacted in logs

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the azure-ops bundle.
