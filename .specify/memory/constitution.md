# hermes-lite Constitution
<!-- Constitution for a privacy-first, security-conscious AI agent that commits to git and deploys to Azure -->

## Core Principles

### I. Privacy-First Design
All agent state, conversation history, and user data MUST remain on the host unless explicitly authorized by the user. Telemetry, logging, and diagnostic uploads MUST be opt-in and disabled by default. Local inference via Ollama is the default path; cloud providers are escalation-only and require explicit provider selection. No remote code execution or dynamic skill loading from unverified network sources is permitted.

### II. Security-Hardened Runtime
Every deployment target (systemd, container) MUST apply defense-in-depth: privilege dropping, filesystem sandboxing, memory limits, and egress filtering. Secrets (API keys, SSH keys, OAuth tokens) MUST be stored in the OS keyring or a restricted file (0600) and MUST never appear in logs or process listings. Git commits MUST be signed (GPG or SSH signing) before push, and the agent MUST verify signatures on pull. Azure deployments MUST use managed identities or workload identity federation; long-lived service principal secrets are prohibited.

### III. Minimal Attack Surface
The dependency tree MUST be the smallest set required for the active feature profile. Removed providers, gateways, and media pipelines MUST NOT be installable via runtime toggles. Containers MUST run as non-root; systemd units MUST use `ProtectHome`, `NoNewPrivileges`, and `RestrictSUIDSGID`. The build manifest (`pyproject.toml`) is the single source of truth for dependencies; no secondary package managers (npm, cargo, nix) are allowed in the production image.

### IV. Observable and Reproducible
All configuration MUST be declarative (YAML) and version-controlled. Infrastructure-as-Code (Bicep or Terraform) MUST define Azure resources; manual portal changes are prohibited in production. CI/CD pipelines MUST produce signed SBOMs for every container image and Python wheel. Changes MUST be committed to git with clear, atomic messages; force-pushes to protected branches are blocked.

### V. User Sovereignty
The user retains full ownership of their data, models, and generated artifacts. The agent MUST support full offline operation; cloud features are optional enhancements. Encryption at rest (LUKS or full-disk encryption) is recommended and MUST be documented in the deployment guide. The agent MUST provide a one-click "purge all state" command that securely wipes `~/.hermes-lite` and all associated journald logs.

## Additional Constraints

### Technology Stack
Python 3.11+ is the sole runtime language for agent logic. systemd 249+ is the minimum for hardened service units. Docker is optional and only used for the `Dockerfile.lite` path. Azure CLI and Bicep are the required deployment tools; Terraform is acceptable where Bicep is unavailable.

### Compliance and Data Handling
No unencrypted secrets may be committed to the repository (enforced by pre-commit hooks and secret-scanning CI jobs). Logs MUST NOT contain PII, API keys, or conversation content without explicit user opt-in. GDPR-aligned data retention defaults to 30 days for diagnostic logs and 90 days for trajectory archives; the user may reduce or disable both.

### Deployment Policy
Production Azure resources MUST use private endpoints where available. Public IP exposure requires documented security review and explicit sign-off. Network security groups and Azure Firewall rules must deny all egress except the allowlisted endpoints defined in `systemd/hermes-lite.service` and `lite-config.yaml`.

### Networking
Egress allowlists are mandatory in every deployment mode. Ingress is minimized to gateway-facing ports (Discord gateway events, Open WebUI host). All inter-service communication inside Azure MUST use private VNet connectivity or managed private endpoints.

## Development Workflow

### Threat Modeling and Review
Every new feature or provider adapter MUST include a lightweight threat model covering data flow, secret handling, and network exposure. All pull requests MUST receive at least one review from a human or a separately instantiated agent with read-only audit scope. Security-sensitive changes (authentication, network policy, provider adapters) MUST pass a dedicated security checklist before merge.

### Dependency and Supply-Chain Management
All Python dependencies MUST be exact-pinned in `pyproject.toml` and hash-verified in `uv.lock`. New dependencies require justification and a security review of their transitives. Unused dependencies MUST be removed within one release cycle. SBOMs are generated automatically in CI and signed before attachment to releases.

### CI/CD Quality Gates
The pipeline MUST enforce: lint (ruff), type-check (ty/pyright), unit tests, container build size check (<350 MB), systemd unit syntax validation, egress rule validation, and signed SBOM generation. Any failure blocks merge.

### Git Hygiene
Commits MUST be atomic and reference the relevant spec number (e.g. `spec/015: add Dockerfile.lite`). Merge commits are discouraged; rebase-and-merge is preferred. Protected branches (`main`, `release/*`) require signed commits and passing CI.

## Governance

This constitution supersedes all other development practices for the hermes-lite project. Amendments require a documented proposal, a security impact assessment, and ratification by the project maintainer. All pull requests and reviews MUST verify compliance with the privacy-first and security-hardened principles. When in doubt, default to the most restrictive interpretation of these rules.

**Version**: 1.0.0 | **Ratified**: 2026-05-24 | **Last Amended**: 2026-05-24
