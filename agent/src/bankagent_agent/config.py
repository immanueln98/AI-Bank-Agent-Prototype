"""Agent configuration + provider factories.

Swapping STT/LLM/TTS is a .env change, never a code change:

    LLM_PROVIDER=inference  LLM_MODEL=openai/gpt-4.1-mini   (default, free credit)
    LLM_PROVIDER=anthropic  LLM_MODEL=claude-haiku-4-5      (direct Anthropic API)

Adding e.g. direct Deepgram/Cartesia plugins later = another branch in the
factories below.
"""

from pathlib import Path
from typing import Literal

from livekit.agents import inference, llm, stt, tts
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    livekit_url: str = ""
    livekit_api_key: str = ""
    livekit_api_secret: str = ""

    llm_provider: Literal["inference", "anthropic"] = "inference"
    llm_model: str = "openai/gpt-4.1-mini"
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

        return anthropic.LLM(model=settings.llm_model)
    return inference.LLM(model=settings.llm_model)


def build_stt(settings: AgentSettings) -> stt.STT:
    return inference.STT(model=settings.stt_model)


def build_tts(settings: AgentSettings) -> tts.TTS:
    if settings.tts_voice:
        return inference.TTS(model=settings.tts_model, voice=settings.tts_voice)
    return inference.TTS(model=settings.tts_model)
