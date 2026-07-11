"""Idle-caller watchdog: prompt a silent caller, then end the call.

Flow (all timings configurable, whole feature toggleable):

    caller silent for IDLE_PROMPT_AFTER_SECONDS
        -> the session's user state becomes "away" (LiveKit user_away_timeout)
        -> agent asks the fixed "are you still there?" line
    caller stays silent for IDLE_HANGUP_AFTER_SECONDS more
        -> agent says a goodbye line, waits for it to play out, deletes the room

Any caller speech cancels the pending hangup and re-arms the cycle (the
framework re-emits "away" after the next silence). If the "away" signal fires
while the agent itself is speaking or thinking - a silent caller listening to
a long answer is not an absent caller - the check is retried shortly instead
of interrupting.

IDLE_TIMEOUT_ENABLED=false disables everything (user_away_timeout is not even
set on the session): essential when pitching with the presenter's mic muted,
where a hangup mid-explanation would end the demo call.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING, Any

from bankagent_shared import get_logger

if TYPE_CHECKING:
    from livekit.agents import AgentSession

log = get_logger(__name__)

IDLE_CHECK_LINE = "Hello? Are you still there?"
IDLE_GOODBYE_LINE = (
    "It seems we've lost you, so I'll end the call here. "
    "Please call back any time you need help. Goodbye."
)

# When "away" fires mid-answer (agent speaking/thinking), re-check this often.
_BUSY_RECHECK_SECONDS = 3.0


class IdleWatchdog:
    """Wired to the session's user_state_changed event in main.py."""

    def __init__(
        self,
        session: AgentSession[Any],
        *,
        hangup_after: float,
        end_call: Callable[[], Coroutine[Any, Any, None]],
    ) -> None:
        self._session = session
        self._hangup_after = hangup_after
        self._end_call = end_call
        self._task: asyncio.Task[None] | None = None
        self.hung_up = False

    def on_user_state(self, new_state: str) -> None:
        if new_state == "away":
            if self._task is None or self._task.done():
                self._task = asyncio.create_task(self._sequence())
        else:
            # The caller is back (any speech flips the state): stand down.
            if self._task is not None and not self._task.done():
                self._task.cancel()
                log.info("idle_sequence_cancelled_user_returned")

    async def _sequence(self) -> None:
        # A silent caller listening to a long answer is not an absent caller.
        while self._session.agent_state in ("speaking", "thinking"):
            await asyncio.sleep(_BUSY_RECHECK_SECONDS)
            if self._session.user_state != "away":
                return

        log.info("idle_prompting_caller")
        await self._session.say(IDLE_CHECK_LINE).wait_for_playout()

        await asyncio.sleep(self._hangup_after)
        # Still away after the grace period: close the call politely.
        self.hung_up = True
        log.info("idle_hangup")
        await self._session.say(IDLE_GOODBYE_LINE).wait_for_playout()
        await self._end_call()
