"""Tool-activity events the agent streams to the demo frontend.

Sent as JSON over a LiveKit text stream on :data:`TOOL_EVENTS_TOPIC`; the
frontend's activity panel renders them live. The TypeScript mirror of this
schema lives in ``frontend/src/lib/types.ts`` - keep the two in sync by hand.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

TOOL_EVENTS_TOPIC = "tool-events"

ToolEventType = Literal[
    "tool_call_started",
    "tool_call_finished",
    "tool_call_failed",
    "identity_verified",
    "escalation",
]


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds")


class ToolEvent(BaseModel):
    type: ToolEventType
    id: str = Field(default_factory=lambda: uuid4().hex)  # pairs started/finished
    tool: str | None = None
    args_masked: dict[str, Any] | None = None  # PII-masked before emission
    result_summary: str | None = None  # short human string, never the raw payload
    error: str | None = None
    duration_ms: int | None = None
    ts: str = Field(default_factory=_now_iso)
