# Tasks: Linux-Only Packaging and systemd Hardening

**Input**: Design documents from `/specs/015-packaging-systemd/`

**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Baseline audit of existing packaging files and verification of current state
- [x] T001 [P] Audit existing `Dockerfile` at repo root — document installed packages, image layers, and uncompressed size
- [x] T002 [P] Audit existing `scripts/install.sh` — document cross-platform branches (macOS, Termux, Windows), size, and identified Linux-only subset
- [x] T003 [P] Audit `pyproject.toml` extras and dependencies — list Windows-only deps, Termux extras, removed-provider extras, and current `[all]` contents
- [x] T004 Verify `scripts/install.ps1` and `scripts/install.cmd` exist and document their removal
- [x] T005 Verify target paths for deletion do not exist in this fork (or confirm they were already removed): `setup-hermes.sh`, `docker-compose.yml`, `nix/`, `packaging/homebrew/`, `flake.nix`, `flake.lock`, `constraints-termux.txt`, `setup.py`
- [x] T006 Read `REDESIGN.md` §7.1-7.3 and capture exact requirements for `Dockerfile.lite`, `systemd/hermes-lite.service`, and `scripts/install.sh`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: `pyproject.toml` cleanup that MUST be complete before `Dockerfile.lite` or `scripts/install.sh` can reference the `[lite]` extra

**⚠️ CRITICAL**: No Dockerfile.lite or install script work can begin until the `[lite]` extra is defined and resolvable

- [x] T007 Remove Windows-only dependencies from `pyproject.toml`: delete `pywinpty==2.0.15; sys_platform == 'win32'` from `[project.optional-dependencies] pty` and the `pty` extra if no longer needed
- [x] T008 Remove `tzdata==2025.3; sys_platform == 'win32'` from `[project.dependencies]` in `pyproject.toml`
- [x] T009 Remove Termux extras from `pyproject.toml`: delete `termux` and `termux-all` optional dependency blocks
- [x] T010 Remove deleted-provider extras from `pyproject.toml`: delete `bedrock`, `azure-identity`, `fal` (if still present and removed by spec 000)
- [x] T011 Remove deleted-gateway extras from `pyproject.toml`: delete `matrix`, `slack`, `dingtalk`, `feishu`, `sms`, `homeassistant` (if removed by spec 001)
- [x] T012 Remove deleted-feature extras from `pyproject.toml`: delete `voice`, `tts-premium`, `edge-tts` (if removed by spec 000/001)
- [x] T013 Define `[lite]` extra in `pyproject.toml` containing only the dependencies required by the lite profile (core deps + anthropic + OpenAI-compatible toolchain + mcp + pty without Windows branch + cron + cli + acp + web + any research deps retained)
- [x] T014 Update `[all]` extra in `pyproject.toml` to only reference Linux-viable extras and exclude deleted providers/gateways
- [x] T015 Update `[project.scripts]` in `pyproject.toml` if any removed entrypoints remain
- [x] T016 Update `[tool.setuptools.package-data]` in `pyproject.toml` to remove references to deleted install scripts (`scripts/install.ps1`)
- [x] T017 Verify `uv lock` (or `pip install -e .[lite]` smoke test) succeeds after pyproject.toml edits

**Checkpoint**: Foundation ready — `[lite]` extra is defined, resolvable, and free of Windows/Termux/removed-provider references. User story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Create Dockerfile.lite for Sub-350 MB Linux Image (Priority: P1) 🎯 MVP

**Goal**: Ship a minimal `Dockerfile.lite` that installs only the `[lite]` extra, `ripgrep`, and optionally `ffmpeg`, producing an uncompressed image under 350 MB

**Independent Test**: Build the image and run `docker images` to verify size <350 MB, then run `docker run --rm hermes-lite hermes-lite --version` without ImportError

### Tests for User Story 1 (OPTIONAL) ⚠️

- [x] T018 [P] [US1] Build test: `docker build -f Dockerfile.lite -t hermes-lite .` completes without error
- [x] T019 [P] [US1] Size test: `docker images hermes-lite` reports SIZE <350 MB
- [x] T020 [P] [US1] Runtime test: `docker run --rm hermes-lite hermes-lite --version` returns version string
- [x] T021 [P] [US1] Tooling test: `docker run --rm hermes-lite which rg` returns path to ripgrep binary

### Implementation for User Story 1

- [x] T022 [US1] Create `Dockerfile.lite` at repository root based on `python:3.11-slim`
  - Multi-stage build or single stage with layer caching optimization
  - Install system deps: `ripgrep`, optionally `ffmpeg` (controlled by `ARG WITH_VOICE=false`)
  - `pip install .[lite]` with `--no-cache-dir`
  - No Node.js, npm, Playwright, dashboard build, `tini`, `docker-cli`, `openssh-client`
  - Set `ENTRYPOINT` to `hermes-lite` or use `CMD` for shell
- [x] T023 [US1] In `Dockerfile.lite`, pin `python:3.11-slim` digest or use explicit platform (`linux/amd64`, `linux/arm64`)
- [x] T024 [US1] Add `.dockerignore` (or update existing) to exclude `tests/`, `ui-tui/`, `website/`, `.git/`, `venv/`, `.venv/` from build context to reduce layer overhead
- [x] T025 [US1] Verify no upstream `Dockerfile` is referenced by CI or docs; replace with `Dockerfile.lite` in any retained build instructions

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Hardened systemd Service Unit (Priority: P2)

**Goal**: Provide `systemd/hermes-lite.service` that runs the gateway under strict resource, filesystem, and network isolation

**Independent Test**: Install unit on a Linux host, start it, verify `systemctl status hermes-lite` shows active, `systemctl show hermes-lite -p MemoryMax` returns 5913968640, and outbound to non-allowlisted hosts is blocked

### Tests for User Story 2 (OPTIONAL) ⚠️

- [x] T026 [P] [US2] Install unit file to `/etc/systemd/system/hermes-lite.service`, run `systemctl daemon-reload && systemctl start hermes-lite`, verify `active (running)`
- [x] T027 [P] [US2] Memory limit test: `systemctl show hermes-lite -p MemoryMax` returns `MemoryMax=5913968640`
- [x] T028 [P] [US2] Filesystem isolation test: write to `/home/user/Downloads` from inside the service cgroup is denied
- [x] T029 [P] [US2] Egress filtering test: `curl` from the service cgroup to a non-allowlisted IP fails
- [x] T030 [P] [US2] Restart policy test: kill the hermes-lite process with `kill -9`, verify systemd restarts it after 30 seconds

### Implementation for User Story 2

- [x] T031 [US2] Create `systemd/hermes-lite.service` with:
  - `ExecStart=hermes-lite gateway --profile lite`
  - `MemoryHigh=4G`, `MemoryMax=5.5G`
  - `ProtectHome=tmpfs`, `ReadWritePaths=%h/.hermes-lite %h/repos`
  - `IPAddressAllow=` list (Ollama 127.0.0.1/32, plus allowlisted cloud endpoints: OpenAI, Copilot, Claude, arXiv, OpenAlex, Discord, Open WebUI host, GitHub HTTPS/SSH, git remotes from workspaces.yaml)
  - `IPAddressDeny=any` (or equivalent fallback) after allowlist
  - `Restart=on-failure`, `RestartSec=30`
  - `StandardOutput=journal`, `StandardError=journal`
  - User and group directives (ideal: dedicated `hermes-lite` user, or `%u` for invoking user)
- [x] T032 [US2] Add inline comments in `systemd/hermes-lite.service` documenting how to edit memory limits for hosts with <5.5 GB RAM
- [x] T033 [US2] Add inline comments in `systemd/hermes-lite.service` noting that `IPAddressAllow`/`IPAddressDeny` work regardless of host firewall backend (`nftables`/`iptables`)
- [x] T034 [US2] Create a helper script or `ExecStartPre=` directive in the unit that ensures `~/.hermes-lite/` and `~/repos/` exist before starting

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Linux-Only Install and Bootstrap Scripts (Priority: P3)

**Goal**: Replace the cross-platform installer with a Linux-only `scripts/install.sh`, and ship Ollama bootstrap and model-pull scripts

**Independent Test**: Run `scripts/install.sh` on a fresh Ubuntu VM, verify `~/.local/bin/hermes-lite` symlink works and `hermes-lite --version` runs; then run bootstrap and pull scripts and verify Ollama health and model presence

### Tests for User Story 3 (OPTIONAL) ⚠️

- [x] T035 [P] [US3] Install script test: on fresh Ubuntu 24.04 VM, `scripts/install.sh` completes in <3 minutes and produces a working `~/.local/bin/hermes-lite`
- [x] T036 [P] [US3] Platform guard test: running `scripts/install.sh` on macOS (or with `uname` mocked to `Darwin`) aborts before creating any files
- [x] T037 [P] [US3] Ollama bootstrap test: on a host without Ollama, `scripts/bootstrap-ollama.sh` downloads, starts, and health-checks `127.0.0.1:11434`
- [x] T038 [P] [US3] Model pull test: `scripts/pull-ministral-3.sh` exits 0 and `ollama list` shows `ministral-3:3b`

### Implementation for User Story 3

- [x] T039 [US3] Rewrite `scripts/install.sh`:
  - Abort immediately if `uname` is not `Linux` (reject Darwin, MSYS, CYGWIN, MINGW, Android/Termux)
  - Require Python 3.11; abort with clear message if absent
  - Create a Python 3.11 venv at `~/.hermes-lite/venv/` (recreate if stale upstream venv detected)
  - `pip install .[lite]` from the repo root
  - Symlink `hermes-lite` entrypoint to `~/.local/bin/hermes-lite`
  - Ensure `~/.local/bin` is on PATH (append to `.bashrc`/`.zshrc` if needed)
  - Do not migrate or touch `~/.hermes`; use `~/.hermes-lite` exclusively
  - Skip all removed providers and gateways
- [x] T040 [US3] In `scripts/install.sh`, make systemd detection graceful: if `systemctl` is missing (e.g. Docker container, WSL1), skip systemd unit installation but still succeed at Python env setup
- [x] T041 [US3] In `scripts/install.sh`, handle pre-existing upstream `venv` by recreating it to avoid stale transitive dependencies from old `[all]` extra
- [x] T042 [US3] Create `scripts/bootstrap-ollama.sh`:
  - Detect if Ollama binary exists; if not, download and install the Linux Ollama binary to `/usr/local/bin/ollama` (or `~/.local/bin/ollama`) using the official install script
  - Start the Ollama daemon (`ollama serve` in background or via systemd if available)
  - Poll `http://127.0.0.1:11434/api/tags` with `curl` until HTTP 200 or timeout (60s)
  - On Jetson without `nvidia-docker` runtime, log a warning suggesting JetPack installation for GPU inference
- [x] T043 [US3] Create `scripts/pull-ministral-3.sh`:
  - Execute `ollama pull ministral-3:3b`
  - Block until the model manifest is present in `~/.ollama/models` (poll `ollama list` or the API)
  - Detect if another pull is in progress and wait for it to complete before initiating
  - Exit 0 only after the model is fully downloaded
- [x] T044 [US3] Mark all three scripts executable (`chmod +x`)

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Strip Cross-Platform and Non-Linux Packaging (Priority: P4)

**Goal**: Remove all upstream packaging artifacts that are not Linux-native and ensure the remaining surface is only Linux packaging files

**Independent Test**: Run `find` queries for deleted filenames and confirm zero matches; verify CI still passes on a Linux-only runner

### Tests for User Story 4 (OPTIONAL) ⚠️

- [x] T045 [P] [US4] Find test: `find . -name 'install.ps1' -o -name 'install.cmd' -o -name 'flake.nix' -o -name 'flake.lock' -o -name 'constraints-termux.txt' -o -name 'setup-hermes.sh' -o -name 'docker-compose.yml' -o -name 'setup.py'` returns zero matches
- [x] T046 [P] [US4] Directory test: `find . -type d -name 'homebrew' -o -type d -name 'nix'` returns zero matches
- [x] T047 [P] [US4] CI test: Linux-only CI pipeline passes after deletions

### Implementation for User Story 4

- [x] T048 [US4] Delete `scripts/install.ps1`
- [x] T049 [US4] Delete `scripts/install.cmd`
- [x] T050 [US4] Delete `scripts/install_psutil_android.py` if it is Termux-specific
- [x] T051 [US4] Update `README.md`:
  - Remove Windows installation instructions and PowerShell/cmd snippets
  - Remove Homebrew (`brew install`) instructions
  - Remove Termux (`pkg install`) instructions
  - Remove Nix (`nix run`) instructions
  - Add a prominent note: "hermes-lite is Linux-only. Windows, macOS, Termux, and Nix are not supported in this fork."
- [x] T052 [US4] Update `pyproject.toml` `[tool.setuptools.package-data]` to remove `scripts/install.ps1` reference if still present
- [x] T053 [US4] Verify `scripts/install.sh` no longer references `install.ps1`, `install.cmd`, Windows, macOS, Termux, Homebrew, or MinGit
- [x] T054 [US4] Verify the repo root contains at most these packaging files: `pyproject.toml`, `Dockerfile.lite`, `systemd/hermes-lite.service`, `scripts/install.sh`, `scripts/bootstrap-ollama.sh`, `scripts/pull-ministral-3.sh`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final verification, documentation, and integration checks

- [x] T055 Build `Dockerfile.lite` and confirm uncompressed image size <350 MB (`docker images`)
- [x] T056 Run `docker run --rm hermes-lite hermes-lite --version` and confirm no ImportError
- [x] T057 Inspect `systemd/hermes-lite.service` for syntax correctness (`systemd-analyze verify systemd/hermes-lite.service` if available)
- [x] T058 Shellcheck `scripts/install.sh`, `scripts/bootstrap-ollama.sh`, `scripts/pull-ministral-3.sh`
- [x] T059 Verify `pyproject.toml` has no remaining `sys_platform == 'win32'` markers
- [x] T060 Verify `pyproject.toml` has no remaining `termux`, `termux-all`, `matrix`, `voice`, `fal`, `bedrock`, `azure-identity` extras (unless explicitly retained by a later spec)
- [x] T061 Run `python -c "import hermes_agent"` or equivalent smoke test after pyproject.toml changes
- [x] T062 [P] Update `REDESIGN.md` §7.1-7.3 references if they differ from delivered artifacts
- [x] T063 [P] Update `specs/015-packaging-systemd/` status to Complete

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories because `Dockerfile.lite` and `scripts/install.sh` both consume the `[lite]` extra
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) — Depends on `[lite]` extra being defined; orthogonal to US1/US2
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) — Deletion and cleanup; can run partially in parallel with US1–US3 but must not delete files still referenced by build scripts

### Within Each User Story

- pyproject.toml edits before Dockerfile.lite or install script
- Dockerfile.lite build verification before declaring US1 complete
- Unit installation before runtime/version test
- Deletion tasks before README update
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- `Dockerfile.lite` (US1) and `systemd/hermes-lite.service` (US2) can be authored in parallel
- All three shell scripts (US3) can be authored in parallel
- Deletion tasks (US4) can run in parallel with script authoring once Foundational is done
- Shellcheck and verification tasks in Phase 7 can run in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (Dockerfile.lite)
4. **STOP and VALIDATE**: Build image, verify <350 MB, run version command
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Dockerfile.lite)
   - Developer B: User Story 2 (systemd unit)
   - Developer C: User Story 3 (install + bootstrap + pull scripts)
   - Developer D: User Story 4 (deletions + README cleanup)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- The `[lite]` extra must be resolvable before any Dockerfile or install script testing
- `~/.hermes-lite/` is the canonical home directory for the fork, distinct from upstream `~/.hermes/`
- If the upstream cross-platform files (`flake.nix`, `setup-hermes.sh`, `docker-compose.yml`, etc.) were already removed in a prior commit, skip the deletion tasks and mark them [x]
