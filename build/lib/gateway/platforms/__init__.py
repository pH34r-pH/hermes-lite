"""
Platform adapters for messaging integrations.

Each adapter handles:
- Receiving messages from a platform
- Sending messages/responses back
- Platform-specific authentication
- Message formatting and media handling

hermes-lite note: Only Discord and Open WebUI are retained as gateway
platform adapters. The TUI uses tui_gateway/ directly.
All other platforms have been removed per REDESIGN.md §4.
"""

from .base import BasePlatformAdapter, MessageEvent, SendResult

__all__ = [
    "BasePlatformAdapter",
    "MessageEvent",
    "SendResult",
]


def load_platforms():
    """Return a mapping of platform names to adapter classes.

    hermes-lite only exposes Discord and Open WebUI gateway adapters.
    The TUI is served through tui_gateway/ directly.
    """
    result = {}
    try:
        from .discord import DiscordAdapter
        result["discord"] = DiscordAdapter
    except Exception:
        pass
    try:
        from .openwebui import OpenWebUIAdapter
        result["openwebui"] = OpenWebUIAdapter
    except Exception:
        pass
    return result
