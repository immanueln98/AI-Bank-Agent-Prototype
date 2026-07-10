"""Agent configuration + provider factories.

Swapping STT/LLM/TTS is a .env change, never a code change:

    LLM_PROVIDER=inference    LLM_MODEL=openai/gpt-4.1-mini   (default, free credit)
    LLM_PROVIDER=anthropic    LLM_MODEL=claude-haiku-4-5      (direct Anthropic API)
    LLM_PROVIDER=self_hosted  LLM_MODEL=<served-model-name>   (on-prem OpenAI-compatible
                                                                server - see below)

self_hosted talks to any OpenAI-compatible chat-completions server - vLLM, TGI, SGLang,
or Ollama all expose this API - via SELF_HOSTED_LLM_BASE_URL. No customer voice or account
data leaves the bank's network on this path: same data-sovereignty argument as running the
STT/TTS on LiveKit's self-hosted media server instead of Cloud, extended to the model
itself. See docs/PITCH.md for the model/hardware recommendation (Mistral Small 3.2 or
Qwen3 on a single 24GB GPU; Llama 3.3 70B FP8 on multi-GPU).

Adding e.g. direct Deepgram/Cartesia plugins later = another branch in the
factories below.

Credentials are passed to the providers explicitly from AgentSettings (which
reads .env), so nothing here depends on the variables being exported into the
process environment - pytest, honcho, and docker all behave the same.
"""

from pathlib import Path
from typing import Literal

from livekit.agents import inference, llm, stt, tts
from livekit.agents.types import NOT_GIVEN
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    livekit_url: str = ""
    livekit_api_key: str = ""
    livekit_api_secret: str = ""

    # Explicit-dispatch identity. Setting a name means the worker no longer
    # auto-joins every room: the browser token endpoint and the SIP dispatch
    # rule both request this agent by name. Must match backend AGENT_NAME.
    agent_name: str = "meridian-bank-agent"

    llm_provider: Literal["inference", "anthropic", "self_hosted"] = "inference"
    llm_model: str = "openai/gpt-4.1-mini"
    anthropic_api_key: SecretStr | None = None  # only when llm_provider=anthropic
    # OpenAI-compatible endpoint for llm_provider=self_hosted, e.g. a vLLM server:
    #   vllm serve mistralai/Mistral-Small-3.2-24B-Instruct-2506 --port 8001
    #   SELF_HOSTED_LLM_BASE_URL=http://localhost:8001/v1
    self_hosted_llm_base_url: str = "http://localhost:8001/v1"
    # Most self-hosted servers don't enforce auth on a private network; only
    # set this if yours does (e.g. an API-gateway in front of the GPU host).
    self_hosted_llm_api_key: SecretStr | None = None
    stt_model: str = "deepgram/nova-3"
    tts_model: str = "cartesia/sonic-3"
    tts_voice: str = ""  # empty = provider default voice

    # Step-up verification (one-time app codes). STEP_UP_ENABLED=false turns
    # it off entirely (single-tier demo; the step-up tools are removed from
    # the agent). When enabled, STEP_UP_MODE places the gate:
    #   actions -> reads need tier-1 only; card blocks/disputes need the code
    #              (risk-proportionate - the production-standard policy)
    #   always  -> the code is required right after tier-1, before ANY
    #              account access (maximal gate, higher friction on every call)
    # Production replaces this static switch with risk-based gating driven by
    # fraud signals (SIM-swap flags, prior fraud markers). Worker restart
    # required after changing either value.
    step_up_enabled: bool = True
    step_up_mode: Literal["actions", "always"] = "actions"

    backend_base_url: str = "http://localhost:8000"
    backend_timeout_seconds: float = 5.0
    transcripts_dir: Path = Path("transcripts")
    log_format: Literal["console", "json"] = "console"


def build_llm(settings: AgentSettings) -> llm.LLM:
    if settings.llm_provider == "anthropic":
        from livekit.plugins import anthropic  # lazy: not needed on the default path

        return anthropic.LLM(
            model=settings.llm_model,
            # NOT_GIVEN falls back to the ANTHROPIC_API_KEY environment variable.
            api_key=settings.anthropic_api_key.get_secret_value()
            if settings.anthropic_api_key
            else NOT_GIVEN,
        )
    if settings.llm_provider == "self_hosted":
        from livekit.plugins import openai  # lazy: not needed on the default path

        return openai.LLM(
            model=settings.llm_model,
            base_url=settings.self_hosted_llm_base_url,
            # vLLM/TGI/SGLang ignore this unless configured to require it, but
            # the OpenAI client requires a non-empty string to be passed.
            api_key=(
                settings.self_hosted_llm_api_key.get_secret_value()
                if settings.self_hosted_llm_api_key
                else "not-required"
            ),
        )
    return inference.LLM(
        model=settings.llm_model,
        api_key=settings.livekit_api_key or None,
        api_secret=settings.livekit_api_secret or None,
    )


def build_stt(settings: AgentSettings) -> stt.STT:
    return inference.STT(
        model=settings.stt_model,
        api_key=settings.livekit_api_key or NOT_GIVEN,
        api_secret=settings.livekit_api_secret or NOT_GIVEN,
    )


def build_tts(settings: AgentSettings) -> tts.TTS:
    return inference.TTS(
        model=settings.tts_model,
        voice=settings.tts_voice or NOT_GIVEN,
        api_key=settings.livekit_api_key or NOT_GIVEN,
        api_secret=settings.livekit_api_secret or NOT_GIVEN,
    )
