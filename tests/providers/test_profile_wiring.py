"""Focused Chat Completions provider-profile integration cases.

Provider-specific request shapes are covered in test_transport_parity.py.
These tests keep separate transport-wiring contracts for disabled reasoning,
message normalization, profile-path role conversion, and request overrides.
"""

import pytest
from agent.transports.chat_completions import ChatCompletionsTransport
from providers import get_provider_profile


@pytest.fixture
def transport():
    return ChatCompletionsTransport()


def _msgs():
    return [{"role": "user", "content": "hello"}]


class TestKimiProfileWiring:
    def test_thinking_disabled(self, transport):
        profile = transport.build_kwargs(
            model="kimi-k2", messages=_msgs(), tools=None,
            provider_profile=get_provider_profile("kimi"),
            reasoning_config={"enabled": False},
        )
        assert profile["extra_body"]["thinking"]["type"] == "disabled"
        assert "reasoning_effort" not in profile


class TestQwenProfileWiring:
    def test_message_preprocessing(self, transport):
        """Qwen profile normalizes string content to list-of-parts."""
        msgs = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "hello"},
        ]
        profile = transport.build_kwargs(
            model="qwen3.5", messages=msgs, tools=None,
            provider_profile=get_provider_profile("qwen"),
        )
        out_msgs = profile["messages"]
        # System message content normalized + cache_control injected
        assert isinstance(out_msgs[0]["content"], list)
        assert out_msgs[0]["content"][0]["type"] == "text"
        assert "cache_control" in out_msgs[0]["content"][-1]
        # User message content normalized
        assert isinstance(out_msgs[1]["content"], list)
        assert out_msgs[1]["content"][0] == {"type": "text", "text": "hello"}


class TestDeveloperRoleProfileWiring:
    def test_profile_path_swaps_for_gpt5(self, transport):
        msgs = [{"role": "system", "content": "Be helpful"}, {"role": "user", "content": "hi"}]
        kw = transport.build_kwargs(
            model="gpt-5.4", messages=msgs, tools=None,
            provider_profile=get_provider_profile("openrouter"),
        )
        assert kw["messages"][0]["role"] == "developer"

    def test_profile_path_no_swap_for_claude(self, transport):
        msgs = [{"role": "system", "content": "Be helpful"}, {"role": "user", "content": "hi"}]
        kw = transport.build_kwargs(
            model="anthropic/claude-sonnet-4.6", messages=msgs, tools=None,
            provider_profile=get_provider_profile("openrouter"),
        )
        assert kw["messages"][0]["role"] == "system"


class TestRequestOverridesProfileWiring:
    def test_extra_body_override_applies_on_profile_path(self, transport):
        kw = transport.build_kwargs(
            model="gpt-5.4", messages=_msgs(), tools=None,
            provider_profile=get_provider_profile("openrouter"),
            request_overrides={"extra_body": {"custom_key": "custom_val"}},
        )
        assert kw["extra_body"]["custom_key"] == "custom_val"

    def test_extra_body_override_merges_with_provider_body(self, transport):
        """Override extra_body merges WITH provider extra_body, not replaces."""
        from agent.portal_tags import nous_portal_tags
        kw = transport.build_kwargs(
            model="hermes-3", messages=_msgs(), tools=None,
            provider_profile=get_provider_profile("nous"),
            request_overrides={"extra_body": {"custom": True}},
        )
        assert kw["extra_body"]["tags"] == nous_portal_tags()  # from profile
        assert kw["extra_body"]["custom"] is True  # from override

    def test_top_level_override(self, transport):
        kw = transport.build_kwargs(
            model="gpt-5.4", messages=_msgs(), tools=None,
            provider_profile=get_provider_profile("openrouter"),
            request_overrides={"top_p": 0.9},
        )
        assert kw["top_p"] == 0.9
