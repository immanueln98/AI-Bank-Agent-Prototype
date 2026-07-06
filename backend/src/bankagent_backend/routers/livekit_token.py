"""LiveKit access-token minting for the demo frontend.

PRODUCTION NOTE: token minting belongs to the bank's channel/auth tier (behind
customer login), not the core-banking API. It lives here only so the POC runs
as one backend process.
"""

from uuid import uuid4

from fastapi import APIRouter
from livekit import api

from bankagent_shared.models import TokenRequest, TokenResponse

from ..config import BackendSettings

router = APIRouter()


@router.post("/livekit/token", response_model=TokenResponse)
def create_token(req: TokenRequest) -> TokenResponse:
    settings = BackendSettings()
    scenario = (req.scenario or "adhoc").strip().lower() or "adhoc"
    room = f"demo-{scenario}-{uuid4().hex[:6]}"
    identity = f"caller-{uuid4().hex[:8]}"

    token = (
        api.AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
        .with_identity(identity)
        .with_name(req.participant_name or "Demo Caller")
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        )
        .to_jwt()
    )
    return TokenResponse(url=settings.livekit_url, token=token, room=room)
