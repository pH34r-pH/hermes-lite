---
name: az-login-status
description: "Return current Azure CLI login state and default subscription."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [azure, az-cli, login, read-only]
    related_skills: [az-account-show, az-resource-list]
---

# az-login-status

## Title
 az-login-status — Azure CLI Login State Inspection

## Description
Call `az account show` via `AzCliWrapper` and return the current Azure CLI login state, subscription name, tenant ID, and authenticated user. If the user is not authenticated, return a clear diagnostic message suggesting `az login` rather than crashing.

## Trigger Conditions
- User invokes `/azure status`
- User asks about Azure login or subscription state

## Inputs
- None (uses ambient Azure CLI session)

## Outputs
- Login state: authenticated or not
- Subscription name, tenant ID, authenticated user principal

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the azure-ops bundle.
