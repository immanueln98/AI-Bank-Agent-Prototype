"""Agent configuration + provider factories.

Swapping STT/LLM/TTS is a .env change, never a code change:

    LLM_PROVIDER=inference  LLM_MODEL=openai/gpt-4.1-mini   (default, free credit)
    LLM_PROVIDER=anthropic  LLM_MODEL=claude-haiku-4-5      (direct Anthropic API)

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

    llm_provider: Literal["inference", "anthropic"] = "inference"
    llm_model: str = "openai/gpt-4.1-mini"
    anthropic_api_key: SecretStr | None = None  # only when llm_provider=anthropic
    stt_model: str = "deepgram/nova-3"
    tts_model: str = "cartesia/sonic-3"
    tts_voice: str = ""  # empty = provider default voice

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
