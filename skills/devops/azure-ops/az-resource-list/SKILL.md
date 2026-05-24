---
name: az-resource-list
description: "Return filtered read-only list of resources in bound subscription/resource group."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [azure, az-cli, resources, read-only]
    related_skills: [az-login-status, az-swa-show]
---

# az-resource-list

## Title
 az-resource-list — Azure Resource Inventory

## Description
Return a filtered, read-only list of resources in the bound subscription and resource group (from the `azure` memory profile). For each resource, return type, location, and provisioning state. Cap at 50 resources and warn if more exist. Must complete within 10 seconds for subscriptions with fewer than 50 resources.

## Trigger Conditions
- User invokes `/azure resources`
- User asks for Azure resource list or inventory

## Inputs
- Bound subscription and resource group from `azure` memory profile

## Outputs
- List of resources with type, location, provisioning state
- Warning if resource count exceeds 50

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the azure-ops bundle.
