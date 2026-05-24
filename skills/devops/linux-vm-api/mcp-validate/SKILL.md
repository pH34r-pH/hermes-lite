---
name: mcp-validate
description: "Validate API MCP surface against hermes-lite mcp/ client skill."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [mcp, api, validation, vm]
    related_skills: [partner-model-health]
---

# mcp-validate

## Title
 mcp-validate — MCP Surface Validation

## Description
Validate the API's MCP surface against the hermes-lite `mcp/` client skill. Report exact incompatibility if found, or confirm compatibility. Ensures the API exposes the expected Model Context Protocol endpoints and schemas.

## Trigger Conditions
- User invokes `/vm mcp validate`
- User asks to check or validate the API MCP surface

## Inputs
- API base URL
- Expected MCP schema or capability list

## Outputs
- Compatibility result: compatible or error list with exact incompatibility details

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the linux-vm-api bundle.
