from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class BackendSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LiveKit Cloud project - used only by the token endpoint.
    livekit_url: str = "wss://not-configured.livekit.cloud"
    livekit_api_key: str = "not-configured"
    livekit_api_secret: str = "not-configured-not-configured-secret"

    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:8080"]
    log_format: Literal["console", "json"] = "console"
    # Where the agent writes masked call transcripts (same default as the
    # agent's AgentSettings.transcripts_dir - shared cwd in dev, shared
    # volume in docker compose).
    transcripts_dir: Path = Path("transcripts")
