"""PartnerProvider — register partner model as remote LM provider.

Registers /v1/partner/chat/completions and /v1/partner/embeddings
via the existing OpenAI-compatible adapter. Places partner model
in the escalation chain after local Ollama, before paid providers.
"""

__version__ = "1.0.0"
