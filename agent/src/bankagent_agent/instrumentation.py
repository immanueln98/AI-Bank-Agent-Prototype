"""Tool-call instrumentation: emits started/finished/failed events per call.

Usage (order matters - ``@function_tool()`` must be outermost so LiveKit sees
the tool; ``functools.wraps`` preserves the name, docstring, and signature the
LLM schema is extracted from):

    @function_tool()
    @emits_tool_events
    async def get_customer_profile(self, context: RunContext[SessionData]) -> ...

The decorated tool must have the standard shape
``(self, context: RunContext[SessionData], ...)``.
"""

from __future__ import annotations

import functools
import inspect
import time
from collections.abc import Awaitable, Callable
from typing import Any
from uuid import uuid4

from livekit.agents import Agent
from livekit.agents.llm import ToolError

from bankagent_shared import ToolEvent

_MAX_SUMMARY_CHARS = 200


def summarize_result(result: Any) -> str:
    """Panel-friendly one-liner - never the raw payload.

    Tools return JSON-able dicts/lists (what the LLM sees), so the shapes are
    recognised by their keys.
    """
    if isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], Agent):
        return str(result[1])  # agent handoff: (next_agent, message)
    if isinstance(result, dict):
        if "accounts" in result and "full_name" in result:  # CustomerProfile
            card = f", card {result['card']['status']}" if result.get("card") else ""
            return f"{result['full_name']}: {len(result['accounts'])} account(s){card}"
        if "replacement_eta_days" in result:  # CardActionResult
            return (
                f"Card ending {result['card_last4']} {result['status']}; replacement "
                f"in {result['replacement_eta_days']} days (ref {result['reference']})"
            )
        if "dispute_id" in result:  # DisputeResult
            return (
                f"Dispute {result['dispute_id']} opened "
                f"({result['status']}, {result['sla_days']}-day SLA)"
            )
        if "ticket_ref" in result:  # EscalationTicket
            return f"Ticket {result['ticket_ref']} raised in queue '{result['queue']}'"
    if isinstance(result, list):
        if not result:
            return "No results"
        if isinstance(result[0], dict):
            if "transaction_id" in result[0]:
                flagged = sum(1 for t in result if t.get("status") == "flagged")
                note = f", {flagged} flagged" if flagged else ""
                return f"{len(result)} transaction(s) returned{note}"
            if "question" in result[0]:
                return f"{len(result)} FAQ match(es); top: {result[0]['question']}"
    text = str(result)
    return text[:_MAX_SUMMARY_CHARS] + ("…" if len(text) > _MAX_SUMMARY_CHARS else "")


def emits_tool_events[F: Callable[..., Awaitable[Any]]](fn: F) -> F:
    signature = inspect.signature(fn)

    @functools.wraps(fn)
    async def wrapper(self: Any, context: Any, *args: Any, **kwargs: Any) -> Any:
        userdata = context.userdata
        emitter = userdata.emitter
        event_id = uuid4().hex
        bound = signature.bind(self, context, *args, **kwargs)
        bound.apply_defaults()
        tool_args = {
            name: value
            for name, value in bound.arguments.items()
            if name not in ("self", "context")
        }
        started_at = time.monotonic()
        await emitter.emit(
            ToolEvent(
                type="tool_call_started", id=event_id, tool=fn.__name__, args_masked=tool_args
            )
        )
        try:
            result = await fn(self, context, *args, **kwargs)
        except ToolError as exc:
            await emitter.emit(
                ToolEvent(
                    type="tool_call_failed",
                    id=event_id,
                    tool=fn.__name__,
                    error=str(exc),
                    duration_ms=int((time.monotonic() - started_at) * 1000),
                )
            )
            raise
        await emitter.emit(
            ToolEvent(
                type="tool_call_finished",
                id=event_id,
                tool=fn.__name__,
                result_summary=summarize_result(result),
                duration_ms=int((time.monotonic() - started_at) * 1000),
            )
        )
        return result

    return wrapper  # type: ignore[return-value]
