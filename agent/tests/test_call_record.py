"""Unit tests for end-of-call record building (outcome classification, audit
roll-up). Pure state-in/record-out - no LiveKit session involved."""

from datetime import UTC, datetime, timedelta
from typing import Any, cast

from bankagent_agent.call_record import build_call_record, derive_outcome, scenario_from_room
from bankagent_agent.session_state import SessionData
from bankagent_shared import ToolEvent


def _userdata(**overrides: Any) -> SessionData:
    data = SessionData(bank=cast(Any, None), emitter=cast(Any, None), known_pii=cast(Any, None))
    data.room_name = "demo-thabo-abc123"
    for key, value in overrides.items():
        setattr(data, key, value)
    return data


class TestDeriveOutcome:
    def test_verified_call_is_contained(self) -> None:
        assert derive_outcome(_userdata(verified=True)) == "contained"

    def test_escalation_trumps_verified(self) -> None:
        assert derive_outcome(_userdata(verified=True, escalated=True)) == "escalated"

    def test_lockout_is_verification_failed(self) -> None:
        data = _userdata(locked_out=True, failed_verification_attempts=3)
        assert derive_outcome(data) == "verification_failed"

    def test_lockout_then_escalation_is_escalated(self) -> None:
        data = _userdata(locked_out=True, escalated=True)
        assert derive_outcome(data) == "escalated"

    def test_never_verified_is_abandoned(self) -> None:
        assert derive_outcome(_userdata()) == "abandoned"


class TestScenarioFromRoom:
    def test_demo_room_parses_scenario(self) -> None:
        assert scenario_from_room("demo-naledi-x1y2z3") == "naledi"

    def test_non_demo_room_is_none(self) -> None:
        assert scenario_from_room("console-room") is None
        assert scenario_from_room("") is None


class TestChannel:
    def test_sip_room_is_tagged_sip(self) -> None:
        data = _userdata(verified=True)
        data.room_name = "call-a1b2c3d4"
        record = build_call_record(data, [])
        assert record.channel == "sip"
        assert record.scenario is None

    def test_demo_room_is_web_and_console_fallback(self) -> None:
        assert build_call_record(_userdata(), []).channel == "web"
        data = _userdata()
        data.room_name = "console-xyz"
        assert build_call_record(data, []).channel == "console"


class TestBuildCallRecord:
    def test_rolls_up_events_into_audit_fields(self) -> None:
        data = _userdata(verified=True, customer_first_name="Thabo", account_masked="****5678")
        data.started_at = datetime.now(UTC) - timedelta(seconds=90)
        events = [
            ToolEvent(type="tool_call_started", tool="verify_identity"),
            ToolEvent(type="tool_call_finished", tool="verify_identity"),
            ToolEvent(type="identity_verified", result_summary="Identity verified"),
            ToolEvent(type="tool_call_started", tool="get_customer_profile"),
            ToolEvent(type="tool_call_finished", tool="get_customer_profile"),
            ToolEvent(type="tool_call_started", tool="get_customer_profile"),
            ToolEvent(type="tool_call_failed", tool="get_customer_profile", error="down"),
        ]
        record = build_call_record(data, events, usage_summary="tokens=123")

        assert record.outcome == "contained"
        assert record.scenario == "thabo"
        assert record.tools_used == ["verify_identity", "get_customer_profile"]  # unique
        assert record.tool_calls == 3
        assert record.tool_failures == 1
        assert record.duration_seconds >= 90
        assert record.events == events
        assert record.usage_summary == "tokens=123"

    def test_lockout_record_carries_security_fields(self) -> None:
        data = _userdata(locked_out=True, failed_verification_attempts=3)
        record = build_call_record(data, [ToolEvent(type="security_lockout")])
        assert record.outcome == "verification_failed"
        assert record.locked_out is True
        assert record.failed_verification_attempts == 3
