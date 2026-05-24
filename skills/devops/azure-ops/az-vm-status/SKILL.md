---
name: az-vm-status
description: "Return VM power state, private IP, and API health endpoint status."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [azure, vm, virtual-machine, read-only, health]
    related_skills: [az-vm-run-command, partner-model-health]
---

# az-vm-status

## Title
 az-vm-status — Virtual Machine Status and Health

## Description
Return the VM power state, private IP, and a badge indicating whether the API health endpoint is responding. Uses `AzCliWrapper` for VM state and `requests` for health endpoint checks.

## Trigger Conditions
- User invokes `/azure vm status`
- User asks for VM health, power state, or IP

## Inputs
- VM name from `azure` memory profile
- API health endpoint URL from `api` memory profile

## Outputs
- VM power state, private IP, API health badge (responding / not responding)

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the azure-ops bundle.
