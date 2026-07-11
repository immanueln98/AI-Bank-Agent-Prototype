"""Unit tests for the idle-caller watchdog (prompt -> grace -> hangup).

A fake session drives the state machine with millisecond timings; the real
wiring (user_away_timeout, event subscription) lives in main.py and is
exercised in live calls.
"""

import asyncio
from typing import Any, cast

import pytest

from bankagent_agent import idle
from bankagent_agent.idle import IDLE_CHECK_LINE, IDLE_GOODBYE_LINE, IdleWatchdog


class _FakeHandle:
    async def wait_for_playout(self) -> None:
        return None


class _FakeSession:
    def __init__(self) -> None:
        self.agent_state = "listening"
        self.user_state = "away"
        self.lines: list[str] = []

    def say(self, line: str) -> _FakeHandle:
        self.lines.append(line)
        return _FakeHandle()


def _watchdog(session: _FakeSession, hangup_after: float = 0.05) -> tuple[IdleWatchdog, list]:
    ended: list[bool] = []

    async def end_call() -> None:
        ended.append(True)

    dog = IdleWatchdog(cast(Any, session), hangup_after=hangup_after, end_call=end_call)
    return dog, ended


async def test_prompts_then_hangs_up_after_grace_period() -> None:
    session = _FakeSession()
    dog, ended = _watchdog(session)

    dog.on_user_state("away")
    await asyncio.sleep(0.2)

    assert session.lines == [IDLE_CHECK_LINE, IDLE_GOODBYE_LINE]
    assert ended == [True]
    assert dog.hung_up is True


async def test_user_returning_cancels_the_hangup() -> None:
    session = _FakeSession()
    dog, ended = _watchdog(session, hangup_after=0.2)

    dog.on_user_state("away")
    await asyncio.sleep(0.05)  # prompt has played; grace period running
    dog.on_user_state("speaking")
    await asyncio.sleep(0.3)

    assert session.lines == [IDLE_CHECK_LINE]  # no goodbye
    assert ended == []
    assert dog.hung_up is False


async def test_waits_for_agent_to_finish_speaking(monkeypatch: pytest.MonkeyPatch) -> None:
    """ "Away" during a long agent answer must not interrupt it - the prompt
    waits until the agent is listening again."""
    monkeypatch.setattr(idle, "_BUSY_RECHECK_SECONDS", 0.02)
    session = _FakeSession()
    session.agent_state = "speaking"
    dog, ended = _watchdog(session)

    dog.on_user_state("away")
    await asyncio.sleep(0.05)
    assert session.lines == []  # still holding back

    session.agent_state = "listening"
    await asyncio.sleep(0.3)
    assert session.lines == [IDLE_CHECK_LINE, IDLE_GOODBYE_LINE]
    assert ended == [True]


async def test_user_return_during_busy_wait_aborts_quietly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(idle, "_BUSY_RECHECK_SECONDS", 0.02)
    session = _FakeSession()
    session.agent_state = "speaking"
    dog, ended = _watchdog(session)

    dog.on_user_state("away")
    session.user_state = "listening"  # user activity resolved the away state
    await asyncio.sleep(0.1)

    assert session.lines == []
    assert ended == []
