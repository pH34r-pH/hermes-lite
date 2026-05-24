---
name: apikey-rotate
description: "Rotate API keys via Key Vault and update systemd unit environment file; never logs secrets."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [api-key, rotation, keyvault, secrets, vm, mutation]
    related_skills: [keyvault-secret-show, systemd-restart]
---

# apikey-rotate

## Title
 apikey-rotate — API Key Rotation

## Description
Rotate API keys via `keyvault-secret-show`, update Azure Key Vault, and update the systemd unit's environment file. Never log the new secret value in agent logs, gateway messages, or `state.db`. Always runs in `approval_mode: confirm` regardless of workspace default. On partial failure (Key Vault updated but systemd file not updated), detect inconsistency, rollback Key Vault change if possible, and emit a failure report.

## Trigger Conditions
- User invokes `/vm rotate-keys`
- User asks to rotate API keys, SSH keys, or Tailscale auth keys

## Inputs
- Key names to rotate
- Key Vault name
- Systemd unit environment file path

## Outputs
- Rotation event metadata (key name, timestamp, initiation source) without key value
- Success or rollback result

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the linux-vm-api bundle.
