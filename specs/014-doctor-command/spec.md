# Feature Specification: `hermes-lite doctor` Command

**Feature Branch**: `014-doctor-command`

**Created**: 2026-05-24

**Status**: Draft

**Input**: User description: "Reduced `hermes-lite doctor` command. Checks: Ollama reachability, credentials, Discord/Open WebUI bindings, TUI availability, state.db schema, skills index, disk space, thermal state/nvpmodel, registered workspaces. Read REDESIGN.md §5.8."

## Current State

Upstream Hermes Agent ships `hermes_cli/doctor.py` (~2000 lines), a comprehensive diagnostic command that checks:

- Python version and virtual environment status.
- Required packages (`openai`, `rich`, `dotenv`, `yaml`, `httpx`) and optional packages (`croniter`, `telegram`, `discord`).
- `~/.hermes/.env` presence and API key configuration.
- `config.yaml` structure and missing keys.
- A large provider health matrix including OpenAI, Anthropic, OpenRouter, Z.AI/GLM, Kimi/Moonshot, StepFun, Arcee AI, GMI Cloud, DeepSeek, Hugging Face, NVIDIA NIM, Alibaba/DashScope, MiniMax, Vercel AI Gateway, Kilo Code, OpenCode Zen, Google/Gemini (OAuth fallback), xAI, MiniMax, and pluggable `plugins/model-providers/` profiles.
- OAuth login status for Gemini, MiniMax, and xAI.
- Gateway service linger (`systemd` user unit).
- Disk space, cronjob availability, browser tooling, ripgrep, Node.js, npm.
- Security advisories with `--ack` support.
- Tool availability per toolset (with special-case overrides for kanban and honcho).
- Model metadata probing.

The upstream doctor is designed for a multi-platform, multi-provider, multi-gateway agent. For hermes-lite, most of these checks are irrelevant because the fork removes the majority of providers, gateways, and heavy dependencies.

## Target State

Hermes-lite ships a reduced `hermes-lite doctor` command that checks only the surfaces and dependencies required for the cyberdeck fork:

1. **Ollama reachability and model presence** — probes `http://127.0.0.1:11434` and verifies the configured default model (e.g., `ministral-3:3b`) is pulled.
2. **Credentials** — checks for `OPENAI_API_KEY`, `GITHUB_COPILOT_TOKEN` (or ACP auth), and `ANTHROPIC_API_KEY` if configured; warns if none are present but does not fail (offline-first operation is valid).
3. **Discord binding** — verifies `discord.py` is importable and a gateway token is configured if Discord is enabled in `lite-config.yaml`.
4. **Open WebUI binding** — verifies the Open WebUI pipeline adapter is importable and the gateway is configured if enabled.
5. **TUI availability** — checks that `ui-tui/` dependencies are installed and the TUI entry point compiles/starts without error.
6. **`state.db` schema version** — validates the SQLite schema matches the expected version for hermes-lite; warns if migration is needed.
7. **Skills index integrity** — runs `ripgrep`-based skill index validation and reports any missing or corrupted bundles required by the active `lite-config.yaml` profile.
8. **Free disk space in `~/.hermes-lite/`** — warns when available space falls below a configurable threshold (default 10 GB on a 512 GB microSD).
9. **Thermal state and `nvpmodel` power mode** — on Jetson, reports CPU/GPU temperature, current `nvpmodel` mode, and throttling status; warns on thermal alarm.
10. **Registered local repo workspaces** — reads `~/.hermes-lite/workspaces.yaml`, verifies each registered workspace exists on disk, and checks whether git authentication is functional (e.g., `ssh -T git@github.com` or `gh auth status`).

The reduced doctor must execute in under 10 seconds on a Jetson Orin Nano. It must reuse the upstream doctor’s output primitives (`check_ok`, `check_warn`, `check_fail`, `_section`) where possible, but live in a new file (`hermes_cli/doctor_lite.py`) or be gated behind a `--lite` flag. The command must not import removed providers or platforms.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Verify Offline-First Baseline (Priority: P1)

A user boots the cyberdeck with no internet and no paid API keys. They run `hermes-lite doctor` and expect a clean bill of health for Ollama, the TUI, and local skills, with informational warnings (not failures) for missing remote credentials.

**Why this priority**: Offline-first is a design premise. The doctor must not block usage when only local resources are available.

**Independent Test**: Can be fully tested by running `hermes-lite doctor` in an environment with no network and no `.env` keys, and verifying it exits 0 with warnings.

**Acceptance Scenarios**:

1. **Given** Ollama is running and `ministral-3:3b` is present, **When** `hermes-lite doctor` runs, **Then** it prints `✓ Ollama reachable` and `✓ Model ministral-3:3b available`
2. **Given** no remote API keys are set, **When** `hermes-lite doctor` runs, **Then** it prints `⚠ No OpenAI/Copilot/Claude credentials configured` (warning, not failure) and exits 0
3. **Given** the TUI is installed and `ui-tui/` dependencies are present, **When** `hermes-lite doctor` runs, **Then** it prints `✓ TUI available`
4. **Given** no network is available, **When** `hermes-lite doctor` runs, **Then** it does not attempt external probes and completes in under 10 seconds

---

### User Story 2 - Detect Local Resource Issues (Priority: P1)

A user notices the agent is sluggish. They run `hermes-lite doctor` and discover that disk space is low and the Jetson is throttling due to temperature.

**Why this priority**: Hardware health directly impacts model inference latency and agent responsiveness. Early warning prevents data loss and thermal damage.

**Independent Test**: Can be fully tested by simulating low disk space and high temperature conditions and verifying the doctor reports them accurately.

**Acceptance Scenarios**:

1. **Given** `~/.hermes-lite/` has less than 10 GB free, **When** `hermes-lite doctor` runs, **Then** it prints `⚠ Disk space low: X GB remaining` and suggests cleanup steps
2. **Given** the Jetson is in `nvpmodel -m 0` (MAXN) and temperature exceeds 85 °C, **When** `hermes-lite doctor` runs, **Then** it prints `⚠ Thermal alarm: CPU Y °C, GPU Z °C` and recommends switching to 25 W mode
3. **Given** `tegrastats` is unavailable (non-Jetson host), **When** `hermes-lite doctor` runs, **Then** it skips the thermal section gracefully with an informational note
4. **Given** `state.db` is missing or the schema is outdated, **When** `hermes-lite doctor` runs, **Then** it prints `✗ state.db schema mismatch` and provides a migration command

---

### User Story 3 - Validate Gateway and Workspace Bindings (Priority: P2)

A user wants to confirm that Discord and Open WebUI are ready to receive prompts, and that the registered git workspaces are authenticated.

**Why this priority**: Gateway binding failures are common setup issues. Verifying them in one command reduces time-to-first-prompt.

**Independent Test**: Can be fully tested by configuring Discord and Open WebUI tokens, registering workspaces, and running the doctor.

**Acceptance Scenarios**:

1. **Given** Discord is enabled and `DISCORD_BOT_TOKEN` is set, **When** `hermes-lite doctor` runs, **Then** it prints `✓ Discord binding configured` (connectivity test is optional; validation of token presence is required)
2. **Given** Open WebUI is enabled and the pipeline adapter is importable, **When** `hermes-lite doctor` runs, **Then** it prints `✓ Open WebUI binding configured`
3. **Given** a workspace `azure-api` is registered at `~/repos/azure-api` but the directory does not exist, **When** `hermes-lite doctor` runs, **Then** it prints `✗ Workspace azure-api path missing` and suggests cloning
4. **Given** a workspace remote requires SSH and the SSH agent has no identities, **When** `hermes-lite doctor` runs, **Then** it prints `⚠ Workspace azure-api git auth unverified` and suggests `ssh-add`

---

### User Story 4 - Skills Index and state.db Validation (Priority: P2)

A user upgrades hermes-lite and wants to verify that the skills index rebuilt correctly and that the session database is compatible.

**Why this priority**: After upgrades or rebases, schema drift and missing skills are the most common causes of silent failures.

**Independent Test**: Can be fully tested by corrupting the skills index, running the doctor, and verifying the failure is reported.

**Acceptance Scenarios**:

1. **Given** the skills index is intact and all required bundles are present, **When** `hermes-lite doctor` runs, **Then** it prints `✓ Skills index valid` with the count of indexed skills
2. **Given** a required skill bundle (e.g., `skills/research/arxiv/`) is missing, **When** `hermes-lite doctor` runs, **Then** it prints `✗ Missing skill bundle: research/arxiv` and exits non-zero
3. **Given** `state.db` schema version matches the expected version, **When** `hermes-lite doctor` runs, **Then** it prints `✓ state.db schema vN`
4. **Given** the user runs `hermes-lite doctor --fix`, **When** `state.db` needs a minor migration, **Then** the doctor attempts the migration automatically and reports success or failure

---

### Edge Cases

- What happens when `lite-config.yaml` is malformed? The doctor must parse it defensively, report the parse error, and skip checks that depend on the config rather than crashing.
- How does the doctor handle a missing Ollama daemon? It prints a clear failure with the command to start it (`sudo systemctl start ollama`) and exits non-zero.
- What happens when the user has no registered workspaces? The workspaces section prints `ℹ No workspaces registered` (informational, not a failure) and points to the registration command.
- How does the doctor behave on non-Jetson hardware? Thermal checks are skipped with a note; power-mode checks are omitted; the remaining checks run unchanged.
- What happens when `ripgrep` is missing? The skills index check degrades to a slower `os.walk` fallback and prints a warning suggesting `sudo apt install ripgrep`.
- How does the doctor handle expired or invalid remote credentials? It performs lightweight presence checks (env var set) but avoids live API calls to prevent rate-limit consumption; a note indicates that live validation is skipped.
- What happens when the TUI build is out of date? The TUI check verifies the compiled bundle exists and the npm/node versions match; if not, it suggests `npm run build` in `ui-tui/`.
- How does the doctor behave when run inside a container? It detects containerized environments (e.g., `/.dockerenv` or `container` cgroup) and skips systemd/thermal checks accordingly.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The command MUST be invocable as `hermes-lite doctor` and MUST complete in under 10 seconds on a Jetson Orin Nano.
- **FR-002**: The command MUST probe Ollama at `http://127.0.0.1:11434` and verify the configured default model is listed in `ollama list`.
- **FR-003**: The command MUST check for the presence of `OPENAI_API_KEY`, `GITHUB_COPILOT_TOKEN` (or ACP auth state), and `ANTHROPIC_API_KEY`; absence MUST be a warning, not a failure.
- **FR-004**: The command MUST verify Discord binding if enabled: `discord.py` importable and `DISCORD_BOT_TOKEN` present.
- **FR-005**: The command MUST verify Open WebUI binding if enabled: pipeline adapter importable and gateway config present.
- **FR-006**: The command MUST verify TUI availability: `ui-tui/` dependencies installed and entry point executable.
- **FR-007**: The command MUST validate `state.db` schema version against the expected hermes-lite schema; mismatches MUST be reported as failures with a migration hint.
- **FR-008**: The command MUST validate the skills index integrity using `ripgrep` (with `os.walk` fallback) and report missing required bundles.
- **FR-009**: The command MUST check free disk space in `~/.hermes-lite/` and warn when below 10 GB (configurable in `lite-config.yaml`).
- **FR-010**: On Jetson, the command MUST report CPU/GPU temperature, current `nvpmodel` mode, and throttling status via `tegrastats`; thermal alarms MUST be warnings.
- **FR-011**: The command MUST read `~/.hermes-lite/workspaces.yaml` and verify each registered workspace path exists and git authentication is functional.
- **FR-012**: The command MUST NOT import or check any removed providers, gateways, or dependencies (e.g., Telegram, Slack, Azure Foundry, AWS Bedrock, Gemini Native).
- **FR-013**: The command MUST support `--fix` to attempt auto-remediation for minor issues (e.g., `state.db` migration, missing `ollama pull`).
- **FR-014**: The command MUST exit 0 when only warnings are present, and non-zero when any check fails (Ollama unreachable, missing required skill bundle, `state.db` unreadable).
- **FR-015**: The command MUST reuse upstream output primitives (`check_ok`, `check_warn`, `check_fail`, `_section`) where available, or reimplement them with identical visual style.

### Key Entities

- **DoctorLite**: The reduced diagnostic command implementation (`hermes_cli/doctor_lite.py` or `--lite` flag).
- **OllamaProbe**: A lightweight HTTP check against `http://127.0.0.1:11434` plus model list validation.
- **CredentialPresenceCheck**: A non-destructive check that verifies API keys are present in the environment without making live API calls.
- **GatewayBindingCheck**: Verification that Discord and Open WebUI adapters are importable and configured.
- **TuiAvailabilityCheck**: Validation that `ui-tui/` dependencies exist and the compiled bundle is present.
- **StateDbSchemaCheck**: A SQLite `PRAGMA user_version` or table-existence check against the expected schema.
- **SkillsIndexCheck**: A scan of `skills/` and `optional-skills/` for required bundles, using `ripgrep` or `os.walk`.
- **DiskSpaceCheck**: A `shutil.disk_usage` check on `~/.hermes-lite/`.
- **ThermalCheck**: A `tegrastats` parser that extracts temperature, power mode, and throttling flags on Jetson.
- **WorkspaceHealthCheck**: A validation of each entry in `workspaces.yaml` for path existence and git authentication.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `hermes-lite doctor` completes in under 10 seconds on a Jetson Orin Nano with no network.
- **SC-002**: An offline-only configuration (Ollama + TUI) exits 0 with warnings for missing remote credentials.
- **SC-003**: A missing Ollama daemon is reported as a failure with a clear remediation command.
- **SC-004**: Thermal alarm conditions (CPU > 85 °C or GPU > 85 °C) are reported as warnings on Jetson.
- **SC-005**: Missing required skill bundles cause a non-zero exit and identify the exact bundle path.
- **SC-006**: `state.db` schema mismatch causes a non-zero exit with a migration command hint.
- **SC-007**: Disk space below 10 GB triggers a warning with the exact bytes remaining.
- **SC-008**: A workspace with a missing path is reported as a failure with the registry path and suggestion to clone.
- **SC-009**: The command does not import any removed provider modules (verified by import-trap test).
- **SC-010**: `--fix` successfully migrates a synthetic old-schema `state.db` and reports success.

## Assumptions

- The user runs `hermes-lite doctor` locally on the cyberdeck or via SSH; remote execution is not a primary use case.
- Ollama is expected to be running on `127.0.0.1:11434`; if it is down, the user is expected to start it manually or via systemd.
- Remote credentials are optional; the doctor warns but does not fail on their absence because offline-first operation is valid.
- The Jetson Orin Nano is the reference thermal platform; non-Jetson hosts gracefully skip thermal checks.
- `ripgrep` is installed by default on the cyberdeck image; if missing, the skills index falls back to `os.walk`.
- Workspaces are registered before the doctor is run; unregistered repos are not checked.
- The doctor command is reduced, not enhanced; new checks are added only if they fit the 10-second budget and the cyberdeck scope.
- Auto-fix (`--fix`) is best-effort and limited to safe, idempotent operations (e.g., schema migration, `ollama pull`); it does not modify user code or config files.
