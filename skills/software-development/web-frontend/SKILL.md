---
name: web-frontend
description: "Root bundle descriptor for web frontend operations. Exposes /web slash command with 4 skills."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [web-frontend, bundle, frontend, static-web-app, astro, nextjs, sveltekit]
    related_skills: [azure-ops, linux-vm-api]
    memory_profiles: [web]
---

# Web-Frontend Skill Bundle

The `web-frontend` bundle provides framework-aware patterns for Astro, Next.js, SvelteKit, or static HTML targeting Azure Static Web Apps. It exposes the `/web` slash command and provides SWA config validation, safe editing, local preview, and Lighthouse-style smoke checks.

## Skill Inventory

1. **staticwebapp-config-validate** — Validate `staticwebapp.config.json` against the SWA schema; report errors with JSON paths
2. **staticwebapp-config-edit** — Safely edit `staticwebapp.config.json` while preserving schema validity; gated by approval
3. **frontend-preview** — Start local preview via `swa start` or `npm run dev`, bound to `localhost` only
4. **frontend-smoke-check** — Run Lighthouse-style checks against deployed SWA URL; report performance, accessibility, and best-practice scores

## Framework Awareness

The bundle detects the workspace framework via `FrameworkDetector`:
- Astro (`astro.config.mjs`)
- Next.js (`next.config.js`)
- SvelteKit (`svelte.config.js`)
- Static HTML (fallback)

On framework mismatch, emit a warning and ask the user to confirm the intended framework before applying patterns.

## Approval Gates

- **config-mutation**: Mandatory before `staticwebapp-config-edit` writes changes

## Memory Profile Bindings

- `web` — Frontend framework conventions and SWA settings

## Safety Rules

- `frontend-preview` binds to `localhost` only; no external network exposure
- Schema validation rejects malformed configs within 2 seconds with exact JSON path
- Smoke check returns clear "not reachable" result for undeployed URLs rather than hanging

## Notes

This is a skeleton bundle. Full skill logic implementation is pending per `specs/008-azure-ops-bundle/`.
