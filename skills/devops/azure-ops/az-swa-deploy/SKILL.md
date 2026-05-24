---
name: az-swa-deploy
description: "Produce deploy artifact and upload to SWA or trigger GitHub Actions workflow."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [azure, swa, static-web-app, deploy, github-actions]
    related_skills: [az-swa-show, az-swa-config-update]
---

# az-swa-deploy

## Title
 az-swa-deploy — Static Web App Deployment

## Description
Produce a deploy artifact from the `web/` build output and upload it via `swa deploy` CLI or trigger the configured GitHub Actions workflow via API. When using GitHub Actions, poll for completion status. On failure, surface error logs and suggest the next diagnostic step. On partial success (upload completes but activation fails), capture the intermediate state, surface both success and failure aspects, and suggest retry or rollback. Pauses for explicit approval before any upload when approval mode is confirm or pr-only.

## Trigger Conditions
- User invokes `/azure swa deploy`
- User asks to deploy the frontend to SWA

## Inputs
- Build output directory (`web/` or configured dist)
- Deploy method: `swa deploy` CLI or GitHub Actions workflow

## Outputs
- Deployment URL or workflow run status
- Error logs and diagnostic suggestions on failure

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the azure-ops bundle.
