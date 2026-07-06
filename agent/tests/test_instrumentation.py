"""Unit tests for the tool-event decorator and result summaries.

The decorator interop with @function_tool (schema extraction) is asserted in
test_tool_schemas.py; here we exercise the runtime event flow with fakes.
"""

from dataclasses import dataclass, field
from typing import Any

import pytest
from livekit.agents.llm import ToolError

from bankagent_agent.instrumentation import emits_tool_events, summarize_result
from bankagent_shared import ToolEvent


class _CapturingEmitter:
    def __init__(self) -> None:
        self.events: list[ToolEvent] = []

    async def emit(self, event: ToolEvent) -> None:
        self.events.append(event)


@dataclass
class _FakeUserdata:
    emitter: _CapturingEmitter = field(default_factory=_CapturingEmitter)


@dataclass
class _FakeContext:
    userdata: _FakeUserdata = field(default_factory=_FakeUserdata)


class _Toolbox:
    @emits_tool_events
    async def lookup(self, context: _FakeContext, account_number: str, limit: int = 5) -> dict:
        return {"ok": True}

    @emits_tool_events
    async def broken(self, context: _FakeContext) -> dict:
        raise ToolError("backend down")


async def test_emits_started_and_finished_with_args() -> None:
    ctx = _FakeContext()
    result = await _Toolbox().lookup(ctx, "1002345678")
    assert result == {"ok": True}

    events = ctx.userdata.emitter.events
    assert [e.type for e in events] == ["tool_call_started", "tool_call_finished"]
    started, finished = events
    assert started.tool == "lookup"
    assert started.args_masked == {"account_number": "1002345678", "limit": 5}
    assert started.id == finished.id  # pairs correlate in the UI
    assert finished.duration_ms is not None


async def test_emits_failed_on_tool_error_and_reraises() -> None:
    ctx = _FakeContext()
    with pytest.raises(ToolError):
        await _Toolbox().broken(ctx)
    events = ctx.userdata.emitter.events
    assert [e.type for e in events] == ["tool_call_started", "tool_call_failed"]
    assert events[1].error == "backend down"


class TestSummarizeResult:
    def test_profile_dict(self) -> None:
        result = {
            "full_name": "Thabo Mokoena",
            "accounts": [{}, {}],
            "card": {"status": "active"},
        }
        assert summarize_result(result) == "Thabo Mokoena: 2 account(s), card active"

    def test_transactions_with_flagged(self) -> None:
        txns = [
            {"transaction_id": "1", "status": "posted"},
            {"transaction_id": "2", "status": "flagged"},
        ]
        assert summarize_result(txns) == "2 transaction(s) returned, 1 flagged"

    def test_card_action(self) -> None:
        out = summarize_result(
            {
                "card_last4": "7742",
                "status": "blocked",
                "replacement_eta_days": 5,
                "reference": "CARD-AB12CD34",
            }
        )
        assert out == "Card ending 7742 blocked; replacement in 5 days (ref CARD-AB12CD34)"

    def test_dispute(self) -> None:
        out = summarize_result({"dispute_id": "DSP-1", "status": "under_review", "sla_days": 10})
        assert "DSP-1" in out and "10-day SLA" in out

    def test_escalation_ticket(self) -> None:
        out = summarize_result({"ticket_ref": "ESC-1", "queue": "general-support"})
        assert "ESC-1" in out

    def test_faq_list(self) -> None:
        out = summarize_result([{"question": "What are your branch hours?", "answer": "..."}])
        assert out.startswith("1 FAQ match(es)")

    def test_empty_list(self) -> None:
        assert summarize_result([]) == "No results"

    def test_long_string_truncated(self) -> None:
        out = summarize_result("x" * 500)
        assert len(out) <= 201


def test_wrapped_tool_preserves_signature_metadata() -> None:
    import inspect

    fn: Any = _Toolbox.lookup
    assert fn.__name__ == "lookup"
    params = list(inspect.signature(fn).parameters)
    assert params == ["self", "context", "account_number", "limit"]
