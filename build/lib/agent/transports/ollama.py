"""Ollama native API transport.

Delegates to the adapter functions and classes in agent/ollama_adapter.py.
This transport owns format conversion and normalization — NOT client lifecycle.
"""

import json
from typing import Any

from agent.transports.base import ProviderTransport
from agent.transports.types import NormalizedResponse, ToolCall, Usage


class OllamaTransport(ProviderTransport):
    """Transport for api_mode='ollama_chat'.

    Wraps the existing OllamaAdapter behind the ProviderTransport ABC.
    """

    @property
    def api_mode(self) -> str:
        return "ollama_chat"

    def convert_messages(self, messages, **kwargs):
        """Ollama accepts OpenAI-format messages directly."""
        return messages

    def convert_tools(self, tools):
        """Tools are injected into the system prompt by the adapter."""
        return tools

    def build_kwargs(
        self,
        model: str,
        messages,
        tools=None,
        **params,
    ):
        """Build kwargs for OllamaAdapter.chat().

        params:
            max_tokens: int | None
            temperature: float | None
            ollama_num_ctx: int | None
            stream: bool
        """
        options = {}
        if params.get("max_tokens") is not None:
            options["num_predict"] = params["max_tokens"]
        if params.get("temperature") is not None:
            options["temperature"] = params["temperature"]
        if params.get("ollama_num_ctx") is not None:
            options["num_ctx"] = params["ollama_num_ctx"]

        return {
            "model": model,
            "messages": messages,
            "tools": tools,
            "stream": params.get("stream", False),
            "options": options,
        }

    def normalize_response(self, response, **kwargs):
        """Normalize an already-OpenAI-compatible SimpleNamespace to NormalizedResponse."""
        if hasattr(response, "choices") and response.choices:
            choice = response.choices[0]
            msg = getattr(choice, "message", getattr(choice, "delta", None))
            finish_reason = getattr(choice, "finish_reason", "stop") or "stop"
        else:
            msg = response.get("message", {}) if isinstance(response, dict) else {}
            finish_reason = (
                response.get("done_reason", "stop") if isinstance(response, dict) else "stop"
            )

        content = getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else None)
        tool_calls = None
        reasoning = getattr(msg, "reasoning", None) or getattr(msg, "reasoning_content", None)

        _tcs = getattr(msg, "tool_calls", None) or (
            msg.get("tool_calls") if isinstance(msg, dict) else None
        )
        if _tcs:
            tool_calls = []
            for tc in _tcs:
                fn = getattr(tc, "function", tc.get("function") if isinstance(tc, dict) else {})
                name = getattr(fn, "name", fn.get("name") if isinstance(fn, dict) else "")
                args = getattr(fn, "arguments", fn.get("arguments") if isinstance(fn, dict) else "{}")
                tool_calls.append(
                    ToolCall(
                        id=getattr(tc, "id", tc.get("id") if isinstance(tc, dict) else None),
                        name=str(name) if name is not None else "",
                        arguments=args if isinstance(args, str) else json.dumps(args),
                    )
                )

        usage = None
        _usage = getattr(response, "usage", None)
        if _usage:
            usage = Usage(
                prompt_tokens=getattr(_usage, "prompt_tokens", 0) or 0,
                completion_tokens=getattr(_usage, "completion_tokens", 0) or 0,
                total_tokens=getattr(_usage, "total_tokens", 0) or 0,
            )

        if finish_reason == "length":
            mapped = "length"
        elif tool_calls:
            mapped = "tool_calls"
        else:
            mapped = "stop"

        return NormalizedResponse(
            content=content,
            tool_calls=tool_calls or None,
            finish_reason=mapped,
            reasoning=reasoning,
            usage=usage,
        )

    def validate_response(self, response) -> bool:
        if response is None:
            return False
        if hasattr(response, "choices"):
            return bool(response.choices)
        if isinstance(response, dict):
            return "message" in response or "response" in response
        return False

    def map_finish_reason(self, raw_reason: str) -> str:
        _MAP = {
            "length": "length",
            "stop": "stop",
        }
        return _MAP.get(raw_reason, "stop")


# Auto-register on import
from agent.transports import register_transport  # noqa: E402

register_transport("ollama_chat", OllamaTransport)
