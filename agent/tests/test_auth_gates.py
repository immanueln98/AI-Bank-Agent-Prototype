"""Unit tests for the tiered-auth gates across STEP_UP mode policies.

Pure state-in/behaviour-out: the gates only touch context.userdata, so a
fake context around a real SessionData exercises every policy branch without
an LLM or LiveKit session.
"""

from dataclasses import dataclass
from typing import Any, cast

import pytest
from livekit.agents.llm import ToolError

from bankagent_agent.agents.banking_agent import (
    _require_read_access,
    _require_step_up,
    effective_step_up_mode,
)
from bankagent_agent.session_state import SessionData


@dataclass
class _FakeContext:
    userdata: SessionData


def _ctx(**overrides: Any) -> _FakeContext:
    data = SessionData(bank=cast(Any, None), emitter=cast(Any, None), known_pii=cast(Any, None))
    data.verified = True
    data.customer_id = "cust-001"
    for key, value in overrides.items():
        setattr(data, key, value)
    return _FakeContext(userdata=data)


class TestEffectiveMode:
    def test_disabled_wins_over_mode(self) -> None:
        ctx = _ctx(step_up_enabled=False, step_up_mode="always")
        assert effective_step_up_mode(ctx.userdata) == "off"

    def test_defaults_to_actions(self) -> None:
        assert effective_step_up_mode(_ctx().userdata) == "actions"


class TestActionGate:
    def test_blocks_until_stepped_up(self) -> None:
        with pytest.raises(ToolError, match=r"[Ss]tep-up"):
            _require_step_up(cast(Any, _ctx()))

    def test_passes_after_step_up(self) -> None:
        ctx = _ctx(step_up_verified=True)
        assert _require_step_up(cast(Any, ctx)) == "cust-001"

    def test_mode_off_degrades_to_tier1(self) -> None:
        ctx = _ctx(step_up_enabled=False)
        assert _require_step_up(cast(Any, ctx)) == "cust-001"

    def test_lockout_refuses_even_after_late_success_flag(self) -> None:
        ctx = _ctx(step_up_locked=True)
        with pytest.raises(ToolError, match="locked"):
            _require_step_up(cast(Any, ctx))

    def test_unverified_caller_is_refused_first(self) -> None:
        ctx = _ctx(verified=False, customer_id=None)
        with pytest.raises(ToolError, match="not identity-verified"):
            _require_step_up(cast(Any, ctx))


class TestReadGate:
    def test_actions_mode_reads_need_tier1_only(self) -> None:
        assert _require_read_access(cast(Any, _ctx())) == "cust-001"

    def test_always_mode_gates_reads_too(self) -> None:
        ctx = _ctx(step_up_mode="always")
        with pytest.raises(ToolError, match=r"[Ss]tep-up"):
            _require_read_access(cast(Any, ctx))

    def test_always_mode_reads_open_after_step_up(self) -> None:
        ctx = _ctx(step_up_mode="always", step_up_verified=True)
        assert _require_read_access(cast(Any, ctx)) == "cust-001"

    def test_off_mode_reads_need_tier1_only(self) -> None:
        ctx = _ctx(step_up_enabled=False, step_up_mode="always")
        assert _require_read_access(cast(Any, ctx)) == "cust-001"
