"""AzCliWrapper — subprocess runner for Azure CLI commands.

Runs `az` commands with timeout, captures stdout/stderr, parses JSON,
scrubs the environment of secrets, and surfaces clear diagnostics.
"""

__version__ = "1.0.0"
