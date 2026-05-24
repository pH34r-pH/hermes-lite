# Feature Specification: Security & Red-Team Ops Kit

**Feature Branch**: `009-security-redteam-bundle`

**Created**: 2026-05-24

**Status**: Draft

**Input**: User description: "New skills/security/red-team/ and blue-team/ bundles. 9 sequential skills from sec-threat-model through sec-rotate-credentials. Self-pentest discipline against agent's own deployed surface. Approval/blast-radius rules. Security memory profile is write-only for /sec kit. Read REDESIGN.md §5.12."

## Current State

Upstream Hermes Agent ships a broad `skills/` tree including `software-development/`, `devops/`, and `github/` skills, but there is **no dedicated security / red-team skill bundle** that performs self-pentest against the agent's own deployed surface. The existing security content is limited to niche optional skills (`optional-skills/security/oss-forensics/`) focused on open-source forensics and password management documentation. There is no native threat-modeling skill, no static secret/dependency scanner, no active auth/web/rate-limit probe harness, no schema-driven fuzzer, no structured findings writer, and no credential-rotation skill. The upstream agent has no concept of a `security` memory profile, no `security-scope.yaml` restricting probe targets to owned hostnames, no per-skill approval/blast-radius rules, and no cross-kit write isolation that prevents non-security kits from contaminating security baselines.

The upstream `agent/tool_guardrails.py` and `agent/file_safety.py` provide generic command and file safety, but they do not implement security-specific constraints such as: blocking probes from reaching non-owned hosts, rate-limiting active probes at the agent layer, or requiring confirmation mode for credential rotation. There is no integration between security findings and the spec-kit bundle — findings cannot emit a `spec-seed.json` to drive a tracked fix through the spec → plan → tasks → PR loop.

## Target State

Hermes-lite ships a complete `skills/security/red-team/` bundle plus a small `skills/security/blue-team/` subtree, exposed through a single `/sec` slash command. The bundle implements 9 sequential skills, each sized for a 3B model context, all targeting **only the agent's own deployed surface** (SWA + VM API + Bicep stack). A `security-scope.yaml` file declares the owned hostnames the kit may probe; the egress filter blocks all other hosts. Active probes (steps 4-7) require workspace `approval_mode` of at least `confirm` and are rate-limited at the agent layer. `sec-rotate-credentials` is always confirmation-mode. Findings never get auto-fixed; they always feed the spec-kit as a `spec-seed.json` so fixes land as tracked PRs. The `security` memory profile is **write-only to the `/sec` kit** and read-only to all other kits, preventing contamination of threat models and baselines.

The blue-team subtree provides passive defense skills: baseline management, log review, and audit-readiness checks that complement the red-team probes.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Produce and Maintain a Threat Model (Priority: P1)

A user asks hermes-lite to review the security posture of the `azure-api` repo. `sec-threat-model` produces or refreshes a STRIDE-style threat model persisted under `security/threat-model.md` in the monorepo and bound to the `security` memory profile.

**Why this priority**: Threat modeling is the foundation of the self-pentest discipline. Without a current threat model, subsequent probes lack scope and priority.

**Independent Test**: Can be fully tested by running `sec-threat-model` against the `azure-api` workspace and verifying that `security/threat-model.md` exists, contains STRIDE categories, and references the actual SWA + VM + Bicep components.

**Acceptance Scenarios**:

1. **Given** the `azure-api` repo contains `infra/`, `web/`, and `api/` sub-trees, **When** `sec-threat-model` runs, **Then** it writes `security/threat-model.md` with STRIDE categories mapped to each component
2. **Given** a threat model already exists, **When** `sec-threat-model` runs again, **Then** it refreshes the model, adds a changelog entry, and updates the memory profile without duplicating existing threats
3. **Given** the user asks for the threat model summary, **When** the `security` memory profile is queried, **Then** it returns the top 5 threats by severity with affected components and mitigation status
4. **Given** the `security` memory profile is queried by a non-security kit (e.g., arxiv kit), **When** read access is attempted, **Then** it succeeds; **When** write access is attempted, **Then** it is refused with a clear error

---

### User Story 2 - Run Static Security Scans (Priority: P1)

A user asks hermes-lite to scan the `azure-api` repo for secrets, dependency CVEs, and Bicep misconfigurations. `sec-static-scan` runs `ripgrep`-based secret scanning, dependency audit (`pip-audit`, `npm audit`, `cargo audit`, `gh advisory`), and Bicep linter passes.

**Why this priority**: Static scanning catches the most common vulnerability classes (leaked secrets, known CVEs, misconfigurations) without touching live services, making it the safest first probe.

**Independent Test**: Can be fully tested by seeding a test repo with a fake secret, a dependency with a known CVE, and a malformed Bicep file, then running `sec-static-scan` and verifying each finding is captured.

**Acceptance Scenarios**:

1. **Given** a test file contains `AWS_SECRET_ACCESS_KEY=AKIA...`, **When** `sec-static-scan` runs, **Then** it flags the secret with file path, line number, and rule name
2. **Given** `package.json` includes a dependency with a known CVE, **When** `npm audit` runs, **Then** the finding appears in the scan output with CVE ID, severity, and recommended version
3. **Given** a Bicep file has a missing required property, **When** the Bicep linter runs, **Then** it emits an error with the property name and resource type
4. **Given** no issues are found, **When** `sec-static-scan` completes, **Then** it emits a clean report and updates the security baseline in the memory profile

---

### User Story 3 - Perform Active Probes Against Owned Surface (Priority: P2)

After static scans pass, the user authorizes active probing. `sec-auth-probe`, `sec-web-probe`, `sec-rate-limit-probe`, and `sec-fuzz` run controlled active tests against the deployed SWA and API, constrained by `security-scope.yaml` and agent-layer rate limits.

**Why this priority**: Active probes validate that the deployed surface behaves securely under real attack patterns. The self-pentest discipline ensures the agent cannot ship a vulnerability and then exploit it.

**Independent Test**: Can be fully tested by running each probe skill against a staging deployment and verifying that no requests escape the hostnames declared in `security-scope.yaml`.

**Acceptance Scenarios**:

1. **Given** `security-scope.yaml` lists `staging-api.example.com`, **When** `sec-auth-probe` runs, **Then** it sends missing-auth requests, expired-token replay, and role-escalation attempts **only** to that hostname
2. **Given** a probe attempts to connect to a hostname not in `security-scope.yaml`, **When** the egress filter intercepts it, **Then** the request is blocked, the probe skill emits a refusal, and the attempt is logged to `logs/security.jsonl`
3. **Given** `sec-rate-limit-probe` runs, **When** it sends burst traffic, **Then** the agent-layer rate limiter caps the request rate to the configured budget and the probe never exceeds it
4. **Given** `sec-fuzz` runs with a fixed iteration budget of 100, **When** it completes, **Then** it has sent exactly 100 requests, recorded the corpus, and written findings with reproduction steps

---

### User Story 4 - Write Findings and Rotate Credentials (Priority: P2)

After probes complete, `sec-findings-write` produces a structured findings report under `security/findings/<date>-<topic>.md` and emits a `spec-seed.json` so the spec-kit can implement fixes. When needed, `sec-rotate-credentials` rotates API keys, SSH keys, and Tailscale auth keys without logging secrets.

**Why this priority**: Findings must feed into the engineering loop to be fixed; credential rotation is the most sensitive operation in the bundle and must be audit-safe.

**Independent Test**: Can be fully tested by running `sec-findings-write` after a deliberate probe finding and verifying the report format and `spec-seed.json` output, then running `sec-rotate-credentials` in dry-run mode.

**Acceptance Scenarios**:

1. **Given** `sec-auth-probe` found a missing-auth endpoint, **When** `sec-findings-write` runs, **Then** it writes `security/findings/2026-05-24-auth-missing.md` containing severity, reproduction steps, and recommended fix
2. **Given** the finding exists, **When** `sec-findings-write` completes, **Then** it emits a `spec-seed.json` in `~/repos/knowledge/seeds/` naming the target repo and referencing the finding
3. **Given** the user requests API key rotation, **When** `sec-rotate-credentials` runs, **Then** it updates Key Vault and the systemd environment file, and the new secret **never** appears in agent logs, gateway messages, or `state.db`
4. **Given** `sec-rotate-credentials` completes, **When** the `security` memory profile is queried, **Then** it records the rotation event (key name, timestamp, initiation source) without the key value

---

### Edge Cases

- What happens when `security-scope.yaml` is missing or empty? All active probe skills must refuse to run and emit a clear error instructing the user to create the scope file before probing.
- How does the system handle a probe that triggers a WAF ban? The agent-layer rate limiter must detect HTTP 403/429 responses, pause the probe, and surface the block to the user rather than retrying aggressively.
- What happens when `sec-static-scan` finds a secret that is actually a test fixture? The scan must support an ignore-list (e.g., `.secretscanignore`) and the finding must be suppressible with a comment annotation.
- How does `sec-fuzz` handle a response that crashes the API? It must stop the fuzz iteration, capture the request that triggered the crash, write it to the corpus, and surface the crash finding immediately.
- What happens when `sec-rotate-credentials` fails partway through (Key Vault updated but systemd file not updated)? The skill must detect the inconsistency, roll back the Key Vault change if possible, and emit a failure report.
- How does the kit handle a finding whose recommended fix spans both `azure-api` and `hermes-lite` repos? The emitted `spec-seed.json` must name a single target repo; cross-repo fixes become two coordinated specs with linked IDs.
- What happens when the blue-team baseline differs from the current scan results? `sec-config-review` must emit a delta report showing changed items, their previous baseline state, and the recommendation.
- How does the system prevent a compromised skill from disabling the egress filter? The egress filter is enforced by the systemd unit (`IPAddressDeny=` / `IPAddressAllow=`) and by `agent/tool_guardrails.py`; neither is mutable by the `/sec` kit or any other skill.

## Requirements *(mandatory)*

### Functional Requirements

#### Red-Team Bundle (`skills/security/red-team/`)

- **FR-001**: `sec-threat-model` MUST produce or refresh a STRIDE-style threat model for the SWA + VM API + Bicep stack, persisted under `<workspace>/security/threat-model.md`
- **FR-002**: `sec-threat-model` MUST bind findings to the `security` memory profile and update a changelog on refresh
- **FR-003**: `sec-static-scan` MUST run `ripgrep`-based secret scanning with configurable ignore-lists and comment annotations
- **FR-004**: `sec-static-scan` MUST run dependency CVE scanning via `pip-audit`, `npm audit`, `cargo audit`, and `gh advisory` as applicable to the workspace
- **FR-005**: `sec-static-scan` MUST run a Bicep linter pass over `infra/` files
- **FR-006**: `sec-config-review` MUST review `staticwebapp.config.json`, CORS rules, CSP headers, reverse-proxy config, systemd hardening, Tailscale ACLs, and Key Vault access policies against a stored baseline
- **FR-007**: `sec-auth-probe` MUST perform active auth checks (missing-auth, expired-token replay, role escalation, CORS pre-flight abuse) against the deployed API
- **FR-008**: `sec-web-probe` MUST perform active web checks (directory listing, broken links, mixed content, open redirect, cookie attributes) against the deployed SWA through `plugins/browser/`
- **FR-009**: `sec-rate-limit-probe` MUST perform controlled burst testing against allowlisted endpoints with a strict iteration budget
- **FR-010**: `sec-fuzz` MUST perform schema-driven fuzzing of API request bodies with a fixed iteration budget and recorded corpus
- **FR-011**: `sec-findings-write` MUST write a structured findings report under `<workspace>/security/findings/<date>-<topic>.md` with reproduction steps, severity, and recommended fix
- **FR-012**: `sec-findings-write` MUST emit a `spec-seed.json` so the spec-kit can implement the fix through the tracked PR loop
- **FR-013**: `sec-rotate-credentials` MUST rotate API keys, SSH keys, and Tailscale auth keys; update Key Vault and the systemd unit environment file; and NEVER log the new secret value
- **FR-014**: `sec-rotate-credentials` MUST always run in `approval_mode: confirm` regardless of workspace default

#### Blue-Team Subtree (`skills/security/blue-team/`)

- **FR-015**: The blue-team subtree MUST provide baseline management: store, compare, and update security baselines for config files and scan results
- **FR-016**: The blue-team subtree MUST provide audit-readiness checks: verify that required security artifacts (`threat-model.md`, `findings/`, `security-scope.yaml`) exist and are up to date
- **FR-017**: The blue-team subtree MUST provide log-review helpers: bounded `journalctl` parsing for security-relevant units, with pattern matching for known attack signatures

#### Approval, Blast-Radius, and Isolation Rules

- **FR-018**: Every active probe (skills 4-7) MUST require workspace `approval_mode` of at least `confirm`
- **FR-019**: Active probes MUST target **only** hostnames declared in `~/.hermes-lite/security-scope.yaml`; the egress filter MUST block all other hosts
- **FR-020**: Active probes MUST be rate-limited at the agent layer in addition to target-enforced limits
- **FR-021**: Findings MUST never be auto-fixed; they MUST feed the spec-kit through `spec-seed.json`
- **FR-022**: The `security` memory profile MUST be **write-only to the `/sec` kit** and **read-only to all other kits**
- **FR-023**: The `security` memory profile MUST be readable by the blue-team subtree for baseline comparison and audit-readiness
- **FR-024**: All `/sec` skills MUST emit structured events to `logs/security.jsonl` with `mode 0600` rotation
- **FR-025**: The security kit MUST bind to the `security` memory profile (write) plus `web`, `api`, and `infra` memory profiles (read)

### Key Entities

- **ThreatModel**: A STRIDE-style markdown document (`security/threat-model.md`) mapping threats to the SWA, VM API, and Bicep components.
- **SecurityScope**: The `~/.hermes-lite/security-scope.yaml` file declaring owned hostnames, API endpoints, and SWA URLs that the red-team kit is permitted to probe.
- **FindingsReport**: A structured markdown document under `security/findings/` containing severity, reproduction steps, and recommended fixes.
- **ProbeBudget**: A per-probe iteration and rate limit enforced at the agent layer, independent of target rate limits.
- **SecurityMemoryProfile**: The `security` memory profile containing threat models, baselines, findings history, and credential rotation events. Write-only for the `/sec` kit; read-only for all other kits.
- **SpecSeed**: A structured JSON envelope produced by `sec-findings-write` and consumed by the spec-kit to drive tracked fixes.
- **BlueTeamBaseline**: A stored snapshot of expected security configurations against which `sec-config-review` compares current state.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `sec-threat-model` produces a valid threat model covering all three components (SWA, VM API, Bicep) within 60 seconds on the Jetson 25 W mode
- **SC-002**: `sec-static-scan` detects at least 90% of seeded secrets and known CVEs in integration testing
- **SC-003**: `sec-auth-probe` and `sec-web-probe` never send a request to a hostname outside `security-scope.yaml` — verified by egress-filter logs
- **SC-004**: `sec-rate-limit-probe` never exceeds its configured request-rate budget — verified by `logs/security.jsonl`
- **SC-005**: `sec-fuzz` records every request in the corpus and stops exactly at the configured iteration budget
- **SC-006**: `sec-findings-write` produces a findings report and a valid `spec-seed.json` within 30 seconds per finding
- **SC-007**: `sec-rotate-credentials` completes a rotation cycle without logging the new secret in any agent log, gateway message, or `state.db` entry
- **SC-008**: The `security` memory profile rejects write attempts from non-security kits with a clear error message
- **SC-009**: A complete security kit pass (threat-model → static-scan → config-review → auth-probe → web-probe → findings-write) completes end-to-end in under 10 minutes on the Jetson 25 W mode for a single-owned-surface target
- **SC-010**: The blue-team subtree detects at least one baseline drift in integration testing when a config file is deliberately altered

## Assumptions

- The target workspace (`azure-api` or `hermes-lite`) is registered in `~/.hermes-lite/workspaces.yaml`
- `~/.hermes-lite/security-scope.yaml` exists and declares at least one owned hostname before active probes are run
- The egress filter (systemd-level and `agent/tool_guardrails.py`) is active and correctly configured
- `plugins/browser/` is available for `sec-web-probe`
- `ripgrep`, `pip-audit`, `npm`, and `cargo` (as applicable) are installed on the cyberdeck
- Azure CLI (`az`) is installed and authenticated for Key Vault access used by `sec-rotate-credentials`
- The `security`, `web`, `api`, and `infra` memory profiles are available
- LocalRepoWorkspace (§5.9) is available for commits of `threat-model.md`, `findings/`, and `security-scope.yaml`
- The spec-kit bundle (§5.10) is available to consume `spec-seed.json` emitted by `sec-findings-write`
- Credential rotation assumes the user has permissions to write to the target Key Vault and systemd environment file
- Active probes assume the target SWA and VM API are reachable from the cyberdeck over the network (Tailscale or public internet)
- The agent never auto-fixes security findings; the user is responsible for reviewing and approving the spec-kit fix cycle
