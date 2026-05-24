---
name: az-vm-run-command
description: "Execute allowed diagnostics commands on VM via Azure Run Command API, gated by per-VM allowlist."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [azure, vm, virtual-machine, run-command, diagnostics]
    related_skills: [az-vm-status, systemd-status]
---

# az-vm-run-command

## Title
 az-vm-run-command — VM Diagnostic Command Execution

## Description
Execute allowed diagnostics commands on the VM through the Azure Run Command API. Commands are gated by `VmAllowlist`; if a command is not on the allowlist, refuse execution and log the refusal at `WARNING` level. Surface stdout/stderr to the user.

## Trigger Conditions
- User invokes `/azure vm run-command <command>`
- User asks to run a diagnostic command on the VM

## Inputs
- Command string to execute
- VM name from `azure` memory profile

## Outputs
- Command stdout/stderr
- Refusal with WARNING log if command is off-allowlist

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the azure-ops bundle.
