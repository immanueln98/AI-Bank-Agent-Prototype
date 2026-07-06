"""Builds the end-of-call operational record posted to the backend.

Pure functions over session state + the (already PII-masked) tool-event log,
so outcome classification is unit-testable without a LiveKit session. The
record feeds the supervisor dashboard: containment vs escalation is the KPI
a call centre actually manages by.
"""

from __future__ import annotations

from datetime import UTC, datetime

from bankagent_shared import ToolEvent
from bankagent_shared.models import CallOutcome, CallRecord

from .session_state import SessionData


def derive_outcome(userdata: SessionData) -> CallOutcome:
    """Classify how the call ended, most-specific outcome first.

    An escalation trumps everything (a human took over, verified or not);
    a lockout is a security outcome, not an abandonment.
    """
    if userdata.escalated:
        return "escalated"
    if userdata.locked_out:
        return "verification_failed"
    if userdata.verified:
        return "contained"
    return "abandoned"


def scenario_from_room(room_name: str) -> str | None:
    """Demo rooms are named ``demo-<scenario>-<suffix>`` by the token endpoint."""
    parts = room_name.split("-")
    if room_name.startswith("demo-") and len(parts) >= 3:
        return parts[1]
    return None


def build_call_record(
    userdata: SessionData,
    events: list[ToolEvent],
    usage_summary: str | None = None,
) -> CallRecord:
    ended_at = datetime.now(UTC)
    tools_used: list[str] = []
    for event in events:
        if event.type == "tool_call_started" and event.tool and event.tool not in tools_used:
            tools_used.append(event.tool)
    return CallRecord(
        session_id=userdata.session_id,
        room=userdata.room_name,
        scenario=scenario_from_room(userdata.room_name),
        started_at=userdata.started_at.isoformat(timespec="seconds"),
        ended_at=ended_at.isoformat(timespec="seconds"),
        duration_seconds=round((ended_at - userdata.started_at).total_seconds(), 1),
        outcome=derive_outcome(userdata),
        verified=userdata.verified,
        customer_first_name=userdata.customer_first_name,
        account_masked=userdata.account_masked,
        failed_verification_attempts=userdata.failed_verification_attempts,
        locked_out=userdata.locked_out,
        escalated=userdata.escalated,
        escalation_ref=userdata.escalation_ref,
        tools_used=tools_used,
        tool_calls=sum(1 for e in events if e.type == "tool_call_started"),
        tool_failures=sum(1 for e in events if e.type == "tool_call_failed"),
        events=events,
        usage_summary=usage_summary,
    )
