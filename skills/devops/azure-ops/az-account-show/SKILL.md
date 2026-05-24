---
name: az-account-show
description: "Return active Azure account details (name, tenant, subscription ID)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [azure, az-cli, account, read-only]
    related_skills: [az-login-status, az-resource-list]
---

# az-account-show

## Title
 az-account-show — Active Azure Account Details

## Description
Return the active Azure account details including name, tenant ID, and subscription ID. Handle unauthenticated state gracefully with a clear error suggesting `az login`.

## Trigger Conditions
- User invokes `/azure account`
- User asks for current Azure account or subscription details

## Inputs
- None (uses ambient Azure CLI session)

## Outputs
- Account name, tenant ID, subscription ID, cloud name

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the azure-ops bundle.
