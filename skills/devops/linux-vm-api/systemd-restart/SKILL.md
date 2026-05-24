---
name: systemd-restart
description: "Restart a specified systemd unit on the VM, gated by user confirmation."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [systemd, vm, restart, mutation]
    related_skills: [systemd-status, journalctl-read]
---

# systemd-restart

## Title
 systemd-restart — Systemd Unit Restart

## Description
Restart a specified systemd unit on the VM. Gated by user confirmation. On failure, read the last 50 lines of `journalctl` for the unit, surface the error, and never attempt to auto-restart without user confirmation.

## Trigger Conditions
- User invokes `/vm systemd restart <unit>`
- User asks to restart a service on the VM

## Inputs
- Unit name to restart
- VM connection via `SystemdClient`

## Outputs
- Restart result: success or failure
- Last 50 lines of journal on failure

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the linux-vm-api bundle.
