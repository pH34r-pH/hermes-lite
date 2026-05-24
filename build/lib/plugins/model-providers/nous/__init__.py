"""Nous Portal provider profile — stubbed in hermes-lite."""

from typing import Any
from providers import register_provider
from providers.base import ProviderProfile


class NousProfile(ProviderProfile):
    """Nous Portal — stubbed in hermes-lite."""

    def build_extra_body(
        self, *, session_id: str | None = None, **context
    ) -> dict[str, Any]:
        return {}

    def build_api_kwargs_extras(
        self,
        *,
        reasoning_config: dict | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        return {}


register_provider(NousProfile(name="nous"))
