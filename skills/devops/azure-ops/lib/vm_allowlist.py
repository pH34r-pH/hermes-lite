"""VmAllowlist — per-VM command allowlist for az-vm-run-command.

Loads allowlist from the `infra` memory profile, matches commands against
patterns, and refuses off-list execution with WARNING logs.
"""

__version__ = "1.0.0"
