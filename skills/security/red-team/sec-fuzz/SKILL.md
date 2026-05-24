---
name: sec-fuzz
description: "Schema-driven fuzzing of API request bodies with fixed iteration budget and recorded corpus."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [security, fuzz, api, red-team, active-probe]
    related_skills: [sec-auth-probe, sec-findings-write]
    memory_profiles: [security, api]
---

# sec-fuzz

## Title
 sec-fuzz — API Fuzzing

## Description
Perform schema-driven fuzzing of API request bodies with a fixed iteration budget. Records every request in the corpus. If a response crashes the API, stop the fuzz iteration immediately, capture the crash-triggering request, write it to the corpus, and surface the crash finding.

## Trigger Conditions
- User invokes `/sec fuzz`
- User asks to fuzz or stress-test the API

## Inputs
- OpenAPI / JSON Schema for request bodies
- Iteration budget (default 100)
- Target endpoint from `security-scope.yaml`

## Outputs
- Fuzz corpus
- Crash findings with reproduction steps
- Structured security events

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the red-team bundle.
