"""Mock core-banking API.

Architecture seam: the voice agent only ever talks to this service over HTTP.
A real deployment replaces the fixture-backed routers with adapters to the
bank's core-banking, card-management, and CRM systems - the agent is untouched.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bankagent_shared import configure_logging

from .config import BackendSettings
from .routers import (
    calls,
    cards,
    customers,
    demo,
    disputes,
    escalations,
    faq,
    livekit_token,
    transcripts,
)


def create_app() -> FastAPI:
    settings = BackendSettings()
    configure_logging(service="bank-backend", fmt=settings.log_format)

    app = FastAPI(
        title="Mock Core Banking API",
        description="Fixture-backed banking API for the voice-agent POC. "
        "Every endpoint marks where a real core-banking integration plugs in.",
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    prefix = "/api/v1"
    app.include_router(customers.router, prefix=prefix, tags=["customers"])
    app.include_router(cards.router, prefix=prefix, tags=["cards"])
    app.include_router(disputes.router, prefix=prefix, tags=["disputes"])
    app.include_router(faq.router, prefix=prefix, tags=["faq"])
    app.include_router(escalations.router, prefix=prefix, tags=["escalations"])
    app.include_router(calls.router, prefix=prefix, tags=["calls"])
    app.include_router(transcripts.router, prefix=prefix, tags=["transcripts"])
    app.include_router(demo.router, prefix=prefix, tags=["demo"])
    app.include_router(livekit_token.router, prefix=prefix, tags=["livekit"])
    return app
