---
name: journalctl-read
description: "Return bounded slice of logs (max 1000 lines) for specified unit; interactive tailing prohibited."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [journalctl, logs, vm, read-only, systemd]
    related_skills: [systemd-status, systemd-restart]
---

# journalctl-read

## Title
 journalctl-read — Bounded Systemd Log Reading

## Description
Return a bounded slice of logs (max 1000 lines) for the specified systemd unit. Interactive tailing is prohibited. Default to returning the last 100 lines. Used by `systemd-restart` to surface errors on failed starts.

## Trigger Conditions
- User invokes `/vm logs <unit>`
- User asks for logs from a VM service

## Inputs
- Unit name
- Line limit (default 100, max 1000)
- Optional time range

## Outputs
- Log lines for the specified unit

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the linux-vm-api bundle.
