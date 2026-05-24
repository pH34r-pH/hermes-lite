"""ProbeBudget — per-probe iteration counter and rate limiter.

Enforces burst ceiling, pauses on HTTP 403/429 responses,
and emits refusal when budget is exhausted.
"""

__version__ = "1.0.0"
