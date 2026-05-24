---
name: sec-rotate-credentials
description: "Rotate API keys, SSH keys, and Tailscale auth keys without logging secrets."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [security, credentials, rotation, keyvault, red-team]
    related_skills: [keyvault-secret-show, sec-findings-write]
    memory_profiles: [security]
---

# sec-rotate-credentials

## Title
 sec-rotate-credentials — Credential Rotation

## Description
Rotate API keys, SSH keys, and Tailscale auth keys. Update Azure Key Vault and the systemd unit environment file. Never log the new secret value in agent logs, gateway messages, or `state.db`. Always run in `approval_mode: confirm` regardless of workspace default. Detect partial failures and rollback Key Vault change if possible.

## Trigger Conditions
- User invokes `/sec rotate-credentials`
- User asks to rotate credentials or secrets

## Inputs
- Key names and types to rotate
- Key Vault name
- Systemd unit environment file path

## Outputs
- Rotation event recorded in `security` memory profile (key name, timestamp, source) without key value
- Success or rollback report

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the red-team bundle.
