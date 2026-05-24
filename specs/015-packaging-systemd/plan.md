# Implementation Plan: Linux-Only Packaging and systemd Hardening

**Branch**: `015-packaging-systemd` | **Date**: 2026-05-24 | **Spec**: `specs/015-packaging-systemd/spec.md`

**Input**: Feature specification from `/specs/015-packaging-systemd/spec.md`

## Summary

Shrink the hermes-lite packaging surface to a Linux-only footprint. Create `Dockerfile.lite` (<350 MB uncompressed) based on `python:3.11-slim`, create a hardened `systemd/hermes-lite.service` unit with `MemoryHigh=4G`/`MemoryMax=5.5G` and egress filtering, replace the cross-platform `scripts/install.sh` with a Linux-only installer, add `scripts/bootstrap-ollama.sh` and `scripts/pull-ministral-3.sh`, strip all Windows/nix/homebrew/termux paths, and update `pyproject.toml` to define the `[lite]` extra. All remaining packaging artifacts must be Linux-native.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: setuptools (build), systemd 249+ (target host), Docker (image build), bash (install scripts)

**Storage**: `~/.hermes-lite/` (runtime state), `~/.ollama/` (model store), `/etc/systemd/system/` (unit file)

**Testing**: pytest for pyproject.toml validation; Docker build for image size; manual Linux host for systemd install

**Target Platform**: Linux (Jetson Orin Nano 8 GB primary reference)

**Project Type**: CLI agent packaging and deployment (container + systemd + shell scripts)

**Performance Goals**: Docker image build completes in under 5 minutes; install script completes on fresh Ubuntu 24.04 in under 3 minutes

**Constraints**: Dockerfile.lite uncompressed image must be <350 MB; systemd unit must harden without breaking legitimate Ollama/local API access; install script must abort on non-Linux platforms before writing any files

**Scale/Scope**: 5 new/modified files (`Dockerfile.lite`, `systemd/hermes-lite.service`, `scripts/install.sh`, `scripts/bootstrap-ollama.sh`, `scripts/pull-ministral-3.sh`) plus pyproject.toml edits and deletions of upstream cross-platform artifacts.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Security-First Development**: systemd unit uses `ProtectHome=tmpfs`, `ReadWritePaths`, and `IPAddressAllow`/`IPAddressDeny` to limit filesystem and network exposure before the agent loop starts. This is mandatory hardening, not optional.
- **Defense in Depth**: Egress filtering in the unit prevents data exfiltration even if the Python process is compromised. Memory capping (`MemoryHigh`/`MemoryMax`) isolates the agent from Ollama's GPU working set.
- **Secure Defaults**: Dockerfile.lite does not install Node.js, npm, Playwright, or the dashboard build pipeline. The install script creates only the `[lite]` venv, not the full `[all]` extra.
- **Dependency Management**: `pyproject.toml` removes Windows-only dependencies (`pywinpty`, `tzdata; sys_platform == 'win32'`), Termux extras, and provider extras that were deleted in earlier specs, reducing the dependency blast radius.

**Result**: PASS — design aligns with all constitution principles.

## Project Structure

### Documentation (this feature)

```text
specs/015-packaging-systemd/
├── plan.md              # This file
├── spec.md              # Feature specification
└── tasks.md             # Concrete task list
```

### Source Code (repository root)

```text
Dockerfile.lite                    # CREATE — minimal image based on python:3.11-slim
systemd/hermes-lite.service        # CREATE — hardened systemd unit
scripts/install.sh                 # REWRITE — Linux-only installer
scripts/bootstrap-ollama.sh        # CREATE — install/start Ollama on Linux
scripts/pull-ministral-3.sh        # CREATE — pull ministral-3:3b via Ollama
pyproject.toml                     # UPDATE — remove Windows/Termux extras, define [lite]
README.md                          # UPDATE — remove Windows/Homebrew/Termux/Nix instructions
scripts/install.ps1                # DELETE — Windows installer
scripts/install.cmd                # DELETE — Windows installer
```

**Structure Decision**: Single project layout. The packaging surface lives at the repository root (`Dockerfile.lite`, `pyproject.toml`) and in `systemd/` and `scripts/` subdirectories. No new subprojects introduced. The upstream `Dockerfile` is replaced by `Dockerfile.lite`; the cross-platform `scripts/install.sh` is rewritten in-place to be Linux-only.

## Complexity Tracking

> No violations. The feature reduces packaging surface by deleting upstream artifacts and creating focused Linux-only replacements. No new subprojects or heavy persistence layers introduced.
