"""Unit tests for the LLM provider factory - especially the self_hosted branch
(data-sovereignty path: an OpenAI-compatible server on the bank's own network,
e.g. vLLM/TGI/SGLang), which has no prior coverage.

Constructing these client objects does no I/O (the network call happens on
first chat request), so building them in a unit test is safe and fast.
"""

from __future__ import annotations

from livekit.plugins import anthropic, openai

from bankagent_agent.config import AgentSettings, build_llm


class TestSelfHostedProvider:
    def test_builds_openai_compatible_client_at_configured_url(self) -> None:
        settings = AgentSettings(
            llm_provider="self_hosted",
            llm_model="mistralai/Mistral-Small-3.2-24B-Instruct-2506",
            self_hosted_llm_base_url="http://gpu-host.internal:8001/v1",
        )
        result = build_llm(settings)
        assert isinstance(result, openai.LLM)
        assert result.model == "mistralai/Mistral-Small-3.2-24B-Instruct-2506"
        assert result.provider == "gpu-host.internal:8001"

    def test_defaults_to_localhost_vllm_port(self) -> None:
        settings = AgentSettings(llm_provider="self_hosted", llm_model="local-model")
        result = build_llm(settings)
        assert isinstance(result, openai.LLM)
        assert result.provider == "localhost:8001"

    def test_missing_api_key_does_not_raise(self) -> None:
        """Self-hosted servers on a private network usually enforce no auth;
        the OpenAI client still requires a non-empty key string to construct."""
        settings = AgentSettings(llm_provider="self_hosted", llm_model="local-model")
        build_llm(settings)  # must not raise

    def test_configured_api_key_is_used_when_gateway_requires_one(self) -> None:
        settings = AgentSettings(
            llm_provider="self_hosted",
            llm_model="local-model",
            self_hosted_llm_api_key="a-real-secret",  # type: ignore[arg-type]
        )
        build_llm(settings)  # must not raise; secret value isn't introspectable post-construction


class TestOtherProvidersUnaffected:
    def test_default_provider_is_inference(self) -> None:
        assert AgentSettings().llm_provider == "inference"

    def test_anthropic_branch_still_builds(self) -> None:
        settings = AgentSettings(
            llm_provider="anthropic",
            llm_model="claude-haiku-4-5",
            anthropic_api_key="a-real-secret",  # type: ignore[arg-type]
        )
        result = build_llm(settings)
        assert isinstance(result, anthropic.LLM)
