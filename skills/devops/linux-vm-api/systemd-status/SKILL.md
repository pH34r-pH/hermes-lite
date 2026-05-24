---
name: systemd-status
description: "Report state of API proxy and partner Ollama systemd units."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [systemd, vm, status, api-proxy, ollama, partner-model]
    related_skills: [systemd-restart, journalctl-read]
---

# systemd-status

## Title
 systemd-status — Systemd Unit Status Reporting

## Description
Report the state of the API proxy systemd unit and the partner Ollama systemd unit using `SystemdClient`. Return `ActiveState`, `SubState`, and `MainPID` for each unit. Must complete within 5 seconds.

## Trigger Conditions
- User invokes `/vm systemd status`
- User asks for service or systemd status on the VM

## Inputs
- Unit names from `infra` memory profile (default: `api-proxy`, `partner-ollama`)

## Outputs
- Unit status: ActiveState, SubState, MainPID for each requested unit

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the linux-vm-api bundle.
