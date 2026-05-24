# Feature Specification: Linux-Only Packaging and systemd Hardening

**Feature Branch**: `015-packaging-systemd`

**Created**: 2026-05-24

**Status**: Draft

**Input**: User description: "Linux-only packaging: Dockerfile.lite (<350 MB), systemd/hermes-lite.service with MemoryHigh=4G/MemoryMax=5.5G, ProtectHome=tmpfs, egress filtering, restart on failure. scripts/install.sh (Linux-only), scripts/bootstrap-ollama.sh, scripts/pull-ministral-3.sh. Remove Windows paths, homebrew, termux, nix, MinGit. Keep only pyproject.toml + Linux Dockerfile/systemd. Read REDESIGN.md §7.1-7.3."

## Current State

The upstream hermes-agent repository ships a bloated, cross-platform packaging surface:

- **Dockerfile**: Multi-stage build based on `debian:13.4`, installs `build-essential`, `curl`, `nodejs`, `npm`, `python3`, `ffmpeg`, `gcc`, `git`, `openssh-client`, `docker-cli`, `tini`, plus Playwright Chromium via `npx`. Image size is well over 1 GB uncompressed.
- **docker-compose.yml**: Defines `gateway` and `dashboard` services with host networking, mounting `~/.hermes`.
- **docker/entrypoint.sh**: Complex privilege-dropping via `gosu`, bootstraps config/skills, optionally starts a dashboard sidecar.
- **setup-hermes.sh**: Supports Termux (Android), Linux, and macOS via `uv`; installs the full `[all]` extras including messaging, matrix, voice, and web.
- **scripts/install.sh**: 82 KB cross-platform installer covering Linux, macOS, Termux, Windows (PowerShell and `cmd.exe` fallbacks), Homebrew, and MinGit. References `install.ps1` and `install.cmd`.
- **packaging/homebrew/**: Contains `hermes-agent.rb` formula and README for macOS Homebrew distribution.
- **nix/**: Full Nix flake with NixOS modules (`nixosModules.nix`), overlays, devShell, checks, and packages (`flake.nix`, `flake.lock`).
- **constraints-termux.txt**: Android/Termux dependency constraints.
- **pyproject.toml**: Contains Windows-only deps (`pywinpty`, `tzdata; sys_platform == 'win32'`), Termux extras (`termux`, `termux-all`), and a broad `[all]` extra.
- **setup.py**: Additional `data_files` declaration for `skills/` and `optional-skills/`.

## Target State

hermes-lite is a Linux-only fork with a minimal packaging footprint:

- **Dockerfile.lite**: Based on `python:3.11-slim`, installs only the `[lite]` extra, `ripgrep`, and optionally `ffmpeg`. Target uncompressed size <350 MB. No Node.js, npm, Playwright, or dashboard build.
- **systemd/hermes-lite.service**: Hardened unit running `hermes-lite gateway --profile lite` with `MemoryHigh=4G`, `MemoryMax=5.5G`, `ProtectHome=tmpfs`, `ReadWritePaths=~/.hermes-lite ~/repos`, egress filtering via `IPAddressAllow`, `Restart=on-failure`, `RestartSec=30`, and journald logging.
- **scripts/install.sh**: Linux-only rewrite of `setup-hermes.sh`. Aborts on non-Linux platforms. Installs only lite dependencies, creates a Python 3.11 venv, and symlinks `hermes-lite` to `~/.local/bin`.
- **scripts/bootstrap-ollama.sh**: Installs the Linux Ollama binary, starts the daemon, and health-checks `127.0.0.1:11434`.
- **scripts/pull-ministral-3.sh**: Pulls `ministral-3:3b` via Ollama and blocks until complete.
- **Removed artifacts**: `setup-hermes.sh`, `scripts/install.ps1`, `scripts/install.cmd`, `packaging/homebrew/`, `nix/`, `flake.nix`, `flake.lock`, `constraints-termux.txt`, `docker-compose.yml`, `setup.py`, and all Windows/Termux/macOS references in `pyproject.toml`.
- **Remaining packaging files**: `pyproject.toml` (single build manifest), `Dockerfile.lite`, `systemd/hermes-lite.service`, and the three scripts above.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create Dockerfile.lite for Sub-350 MB Linux Image (Priority: P1)

Hermes-lite must ship a minimal `Dockerfile.lite` based on `python:3.11-slim` that installs only the `[lite]` Python extra, `ripgrep`, and optionally `ffmpeg` (when voice is enabled). The resulting uncompressed image must stay under 350 MB. Ollama is expected to run on the host or in a sibling container.

**Why this priority**: The cyberdeck target (Jetson Orin Nano 8 GB) has severe disk and memory constraints. A sub-350 MB image is the foundational deliverable for every other deployment story (container, systemd, install script).

**Independent Test**: Can be fully tested by building the image and running `docker images` to verify the uncompressed size is <350 MB, then starting a container and confirming `hermes-lite --version` runs without error.

**Acceptance Scenarios**:

1. **Given** the repo contains `Dockerfile.lite`, **When** the image is built with `docker build -f Dockerfile.lite -t hermes-lite .`, **Then** the resulting image size is less than 350 MB uncompressed
2. **Given** voice is disabled (default), **When** the image is built, **Then** `ffmpeg` is not installed and the image size is minimized
3. **Given** the image is built, **When** a container starts with `docker run --rm hermes-lite hermes-lite --version`, **Then** the command returns the version string without ImportError
4. **Given** the image is built, **When** running inside the container, **Then** `ripgrep` is available on PATH for skill indexing and `@folder` references
5. **Given** the upstream `Dockerfile` installs Node.js, npm, Playwright, and many system packages, **When** `Dockerfile.lite` is used, **Then** none of those packages are present and the image layer count is reduced

---

### User Story 2 - Hardened systemd Service Unit (Priority: P2)

Hermes-lite must provide a `systemd/hermes-lite.service` unit that runs `hermes-lite gateway --profile lite` under strict resource and filesystem isolation. The unit pins memory with `MemoryHigh=4G` and `MemoryMax=5.5G`, uses `ProtectHome=tmpfs` plus `ReadWritePaths=~/.hermes-lite ~/repos`, filters egress to an allowlisted set of endpoints, restarts on failure with a 30-second backoff, and logs to journald.

**Why this priority**: On the Jetson Orin Nano, the 8 GB unified memory pool is shared between CPU, GPU, and OS. Without systemd hardening, a runaway Python process or memory leak could evict the Ollama model from GPU memory or crash the device. Egress filtering prevents data exfiltration.

**Independent Test**: Can be fully tested by installing the unit on a Linux host, starting it with `systemctl start hermes-lite`, and verifying via `systemctl status hermes-lite` that it is active, within memory limits, and that outbound connections to non-allowlisted hosts are blocked.

**Acceptance Scenarios**:

1. **Given** the unit file is installed at `/etc/systemd/system/hermes-lite.service`, **When** `systemctl daemon-reload && systemctl start hermes-lite` is run, **Then** the service enters the `active (running)` state and `journalctl -u hermes-lite` shows startup logs
2. **Given** the service is running, **When** a memory-intensive task causes RSS to approach 5.5 GB, **Then** systemd invokes the OOM killer on the hermes-lite cgroup before the host swaps excessively
3. **Given** the service is running, **When** a process inside the unit attempts to write to `/home/user/Downloads`, **Then** the write is denied because `ProtectHome=tmpfs` only exposes `~/.hermes-lite` and `~/repos` via `ReadWritePaths`
4. **Given** the service is running, **When** a process attempts to connect to an external host not in the allowlist (e.g. `example.com`), **Then** the connection is blocked by the egress filter and a DENIED log line appears in the journal
5. **Given** the service crashes with a non-zero exit code, **When** systemd observes the failure, **Then** it waits 30 seconds and restarts the service automatically
6. **Given** the service is running, **When** it writes logs, **Then** all output is captured by journald and is queryable via `journalctl -u hermes-lite`

---

### User Story 3 - Linux-Only Install and Bootstrap Scripts (Priority: P3)

Hermes-lite must replace the cross-platform `setup-hermes.sh` and upstream `scripts/install.sh` with a Linux-only `scripts/install.sh` that installs the lite extras, skips every removed provider and gateway, and symlinks `hermes-lite` into `~/.local/bin`. It must also ship `scripts/bootstrap-ollama.sh` to install or start Ollama on Linux, and `scripts/pull-ministral-3.sh` to pull the default model.

**Why this priority**: The upstream installer supports Termux, macOS, Windows (PowerShell), and Homebrew. For the lite fork, these are dead weight and create support surface. A focused Linux installer reduces complexity and tunes the first-boot experience for the target hardware.

**Independent Test**: Can be fully tested on a fresh Ubuntu/Debian VM or Jetson by running `scripts/install.sh`, then `scripts/bootstrap-ollama.sh`, then `scripts/pull-ministral-3.sh`, and finally starting `hermes-lite gateway --profile lite`.

**Acceptance Scenarios**:

1. **Given** a fresh Linux server with Python 3.11 and `curl` installed, **When** `scripts/install.sh` is run, **Then** it creates a virtual environment, installs only the `[lite]` extra, and symlinks `hermes-lite` to `~/.local/bin/hermes-lite`
2. **Given** `scripts/install.sh` is running, **When** it detects a non-Linux platform (e.g. `uname` returns `Darwin` or `MSYS`), **Then** it aborts with a clear error message before installing anything
3. **Given** Ollama is not installed, **When** `scripts/bootstrap-ollama.sh` is run, **Then** it downloads and installs the Linux Ollama binary, starts the daemon, and verifies the API endpoint at `127.0.0.1:11434` responds with HTTP 200
4. **Given** Ollama is running, **When** `scripts/pull-ministral-3.sh` is run, **Then** it executes `ollama pull ministral-3:3b` and exits 0 only after the model is fully downloaded and its manifest is present in `~/.ollama/models`
5. **Given** the upstream `scripts/install.ps1`, `scripts/install.cmd`, `packaging/homebrew/`, `nix/`, and `constraints-termux.txt` exist in the repo, **When** the cleanup is applied, **Then** all of those files and directories are deleted and `git status` shows them as removed

---

### User Story 4 - Strip Cross-Platform and Non-Linux Packaging (Priority: P4)

Hermes-lite must remove all upstream packaging artifacts that are not Linux-native: Windows installer paths (`scripts/install.ps1`, `scripts/install.cmd`), Homebrew formula (`packaging/homebrew/`), Nix flake and modules (`nix/`, `flake.nix`, `flake.lock`), Termux constraints (`constraints-termux.txt`), and MinGit references. The remaining packaging surface must be only `pyproject.toml`, `Dockerfile.lite`, `systemd/hermes-lite.service`, and the three scripts.

**Why this priority**: This cleanup prevents the fork from shipping dead code. Retaining Homebrew, Nix, or Windows paths implies support guarantees we do not intend to provide. Removing them shrinks the repo and eliminates CI jobs that test those platforms.

**Independent Test**: Can be fully tested by running `find` queries for the removed filenames and confirming zero matches, then verifying that the CI pipeline still passes on a Linux-only runner after the deletions.

**Acceptance Scenarios**:

1. **Given** the repo root contains `flake.nix` and `flake.lock`, **When** the cleanup is applied, **Then** both files are deleted
2. **Given** the repo contains `packaging/homebrew/hermes-agent.rb`, **When** the cleanup is applied, **Then** the `packaging/` directory is removed entirely
3. **Given** the repo contains `scripts/install.ps1` and `scripts/install.cmd`, **When** the cleanup is applied, **Then** both files are deleted
4. **Given** the repo contains `constraints-termux.txt`, **When** the cleanup is applied, **Then** the file is deleted
5. **Given** `pyproject.toml` contains Windows-specific optional dependencies (e.g. `pywinpty`, `tzdata; sys_platform == 'win32'`), **When** the cleanup is applied, **Then** those dependencies are removed and the `[all]` extra no longer references them
6. **Given** the README mentions Windows, Homebrew, Termux, or Nix installation paths, **When** the cleanup is applied, **Then** those sections are replaced with a prominent note that hermes-lite is Linux-only

---

### Edge Cases

- What happens when `scripts/install.sh` is run on a system without `systemd` (e.g. a Docker container or WSL1)? The script must still succeed at installing the Python environment and symlinking the binary; Ollama bootstrap must be optional and detect the absence of systemd gracefully.
- What happens when `Dockerfile.lite` is built on an architecture other than `linux/amd64` or `linux/arm64`? The base image `python:3.11-slim` supports those; other architectures should fail fast at build time with a clear message, or the build should be restricted to supported platforms.
- What happens when the host Ollama daemon is not reachable from the container? The containerized `hermes-lite` must start and log a clear error rather than crashing in a loop. The `systemd` unit's `RestartSec=30` prevents tight restart loops if Ollama is down.
- What happens when `MemoryMax=5.5G` is set on a host with less than 5.5 GB RAM? systemd will enforce the limit anyway, but the process may be OOM-killed sooner. The unit file must document how to edit the limits for smaller hosts.
- How does the system handle egress filtering on hosts where `nftables` is not available? The unit file must use `IPAddressDeny=` / `IPAddressAllow=` (systemd native), which works regardless of the host firewall backend, with comments guiding manual `iptables`/`nftables` configuration on older systemd versions.
- What happens when a user tries to invoke the old `setup-hermes.sh` after the rename? The old file must be deleted; if a user has bookmarked it, they will get a "file not found" error, which is acceptable for a fork with breaking changes.
- What happens when `scripts/bootstrap-ollama.sh` runs on a Jetson with CUDA but no `nvidia-docker` runtime? The script installs the standard Linux Ollama binary, which will use CPU inference if the CUDA runtime is missing. A warning must be logged suggesting JetPack installation.
- How does the install script handle a pre-existing upstream `~/.hermes` directory? The lite fork uses `~/.hermes-lite` as its home (see spec 005-lite-config). The install script must not migrate or overwrite `~/.hermes`; it must create `~/.hermes-lite` independently.
- What happens when `scripts/pull-ministral-3.sh` is run while another model download is in progress? The script must detect an active pull and wait for it to complete before initiating its own, or exit with a clear message.
- What happens when `scripts/install.sh` finds an existing `venv` from a previous upstream install? It must recreate the venv to avoid stale transitive dependencies from the old `[all]` extra.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create `Dockerfile.lite` based on `python:3.11-slim` that installs only the `[lite]` Python extra (or equivalent minimal dependency set), `ripgrep`, and optionally `ffmpeg` if voice is enabled
- **FR-002**: `Dockerfile.lite` MUST produce an uncompressed image smaller than 350 MB
- **FR-003**: `Dockerfile.lite` MUST NOT install Node.js, npm, Playwright, or the upstream web dashboard build pipeline
- **FR-004**: System MUST create `systemd/hermes-lite.service` that executes `hermes-lite gateway --profile lite` under a dedicated user or the invoking user
- **FR-005**: `systemd/hermes-lite.service` MUST set `MemoryHigh=4G` and `MemoryMax=5.5G`
- **FR-006**: `systemd/hermes-lite.service` MUST set `ProtectHome=tmpfs` and `ReadWritePaths=~/.hermes-lite ~/repos`
- **FR-007**: `systemd/hermes-lite.service` MUST restrict egress with `IPAddressAllow=` to the allowlisted endpoints (Ollama, OpenAI, Copilot, Claude, arXiv, OpenAlex, Discord, Open WebUI host, GitHub HTTPS + SSH, and any additional git remotes declared in `workspaces.yaml`)
- **FR-008**: `systemd/hermes-lite.service` MUST set `Restart=on-failure` and `RestartSec=30`
- **FR-009**: `systemd/hermes-lite.service` MUST log to journald (`StandardOutput=journal`, `StandardError=journal`)
- **FR-010**: System MUST create `scripts/install.sh` that is Linux-only and aborts with a clear error on non-Linux platforms
- **FR-011**: `scripts/install.sh` MUST install only the lite dependency set (no removed providers, no messaging gateways except Discord/Open WebUI, no image/video generation)
- **FR-012**: `scripts/install.sh` MUST create a Python 3.11 virtual environment and symlink `hermes-lite` into `~/.local/bin`
- **FR-013**: System MUST create `scripts/bootstrap-ollama.sh` that installs the Linux Ollama binary, starts the service, and health-checks `127.0.0.1:11434`
- **FR-014**: System MUST create `scripts/pull-ministral-3.sh` that pulls `ministral-3:3b` via the local Ollama API and blocks until completion
- **FR-015**: System MUST delete `scripts/install.ps1`, `scripts/install.cmd`, `packaging/homebrew/`, `nix/`, `flake.nix`, `flake.lock`, `constraints-termux.txt`, `setup-hermes.sh`, and `docker-compose.yml`
- **FR-016**: `pyproject.toml` MUST remove Windows-only dependencies (`pywinpty`, `tzdata; sys_platform == 'win32'`) and extras that are not part of the lite profile (`termux`, `termux-all`, `matrix`, `voice`, `fal`, `bedrock`, `azure-identity`, etc., as defined by earlier provider-cleanup specs)
- **FR-017**: System MUST update `README.md` to remove Windows, Homebrew, Termux, and Nix installation instructions, replacing them with a note that hermes-lite is Linux-only
- **FR-018**: System MUST delete `setup.py` so that `pyproject.toml` is the sole build manifest

### Key Entities

- **Dockerfile.lite**: Minimal container definition for the lite fork. Replaces the upstream `Dockerfile`.
- **systemd/hermes-lite.service**: Hardened systemd unit for running the gateway on Linux devices with resource constraints.
- **scripts/install.sh**: Linux-only setup script. Replaces `setup-hermes.sh` and the cross-platform upstream `scripts/install.sh`.
- **scripts/bootstrap-ollama.sh**: One-shot script to provision the Ollama daemon on a fresh Linux host.
- **scripts/pull-ministral-3.sh**: One-shot script to prefetch the default quantized model.
- **LiteDependencySet**: The curated list of Python extras that belong in the lite install. Excludes all removed providers, media generation, and non-Linux terminals.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `docker build -f Dockerfile.lite -t hermes-lite .` produces an image reported by `docker images` as `<350 MB` uncompressed
- **SC-002**: A container started from the image successfully runs `hermes-lite --version` in under 5 seconds with no ImportError
- **SC-003**: `systemctl start hermes-lite` on a Linux host brings the service to `active (running)` state within 10 seconds, and `systemctl show hermes-lite -p MemoryMax` returns `MemoryMax=5913968640` (5.5 GB)
- **SC-004**: An outbound `curl` from the service cgroup to a non-allowlisted IP fails, while a curl to `127.0.0.1:11434` (Ollama) succeeds
- **SC-005**: `scripts/install.sh` completes on a fresh Ubuntu 24.04 VM in under 3 minutes, producing a working `~/.local/bin/hermes-lite` symlink
- **SC-006**: After running `scripts/bootstrap-ollama.sh` and `scripts/pull-ministral-3.sh`, `ollama list` shows `ministral-3:3b` and `curl http://127.0.0.1:11434/api/tags` returns HTTP 200
- **SC-007**: `find` for the deleted files (`install.ps1`, `install.cmd`, `flake.nix`, `constraints-termux.txt`, `setup-hermes.sh`, `packaging/homebrew/hermes-agent.rb`, `docker-compose.yml`) returns zero matches
- **SC-008**: The repo root contains at most five packaging-related files: `pyproject.toml`, `Dockerfile.lite`, `systemd/hermes-lite.service`, `scripts/install.sh`, `scripts/bootstrap-ollama.sh`, `scripts/pull-ministral-3.sh` (plus `README.md` and `lite-config.yaml`)
- **SC-009**: CI passes on a Linux-only runner after the deletions (no Homebrew, no Nix, no Windows jobs)

## Assumptions

- The target host runs a Linux distribution with systemd version 249 or newer (supports `MemoryHigh`, `MemoryMax`, `ProtectHome=tmpfs`, and `IPAddressAllow`/`IPAddressDeny`)
- The Jetson Orin Nano 8 GB is the primary reference hardware; memory limits are sized for its unified memory pool minus Ollama's working set
- Ollama is installed on the host or in a sibling container; `Dockerfile.lite` does not bundle Ollama
- The `[lite]` extra in `pyproject.toml` is defined by earlier specs (000-provider-cleanup, 001-gateway-cleanup) and is resolvable without git+https dependencies
- The user running the install script has passwordless `sudo` or root access only for the systemd install step; the Python environment itself is installed user-local
- `~/.local/bin` is on PATH or the install script appends it to `.bashrc`/`.zshrc`
- GitHub (HTTPS and SSH) is the only required git remote for the lite fork; additional remotes are declared in `workspaces.yaml` and parsed by the install script or systemd generator
- No backward compatibility is required with upstream Windows, macOS, Termux, or Nix users; this is a hard fork
- The lite fork does not ship the web dashboard or TUI build pipeline inside the container; any UI needs are served by Open WebUI or Discord gateway
- The lite fork uses `~/.hermes-lite` as its home directory, distinct from upstream `~/.hermes`, to prevent accidental state mixing
