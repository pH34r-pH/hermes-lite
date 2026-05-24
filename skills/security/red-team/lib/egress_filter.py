"""EgressFilter — block probes from reaching non-owned hosts.

Loads owned hostnames from ~/.hermes-lite/security-scope.yaml,
intercepts requests from red-team skills, and blocks non-owned hosts.
Immutable at runtime by skill code.
"""

__version__ = "1.0.0"
