"""Tools available at EVERY conversation stage (verified or not).

Mixed into both agents: general-banking FAQ lookup and the human-handoff
escalation. Neither discloses account data.
"""

from __future__ import annotations

from typing import Any

from livekit.agents import RunContext, function_tool
from livekit.agents.llm import ToolError

from bankagent_shared import ToolEvent

from ..bank_client import BankAPIError
from ..instrumentation import emits_tool_events
from ..session_state import SessionData

FALLBACK_LINE = (
    "The banking system could not complete that request right now. "
    "Apologise briefly and offer to connect the customer to a consultant."
)


class SupportToolsMixin:
    @function_tool()
    @emits_tool_events
    async def search_faq(
        self, context: RunContext[SessionData], query: str
    ) -> list[dict[str, Any]]:
        """Search the bank's general FAQ for questions that need no account access,
        such as branch hours, fees, limits, or how banking products work.

        Args:
            query: The customer's question in plain words.
        """
        try:
            results = await context.userdata.bank.search_faq(query)
        except BankAPIError as exc:
            raise ToolError(FALLBACK_LINE) from exc
        return [r.model_dump(mode="json") for r in results]

    @function_tool()
    @emits_tool_events
    async def escalate_to_human(
        self, context: RunContext[SessionData], reason: str, summary: str
    ) -> str:
        """Transfer the caller to a human consultant. Use when the customer asks for
        a person, when you cannot help within your scope, or after repeated failures.

        Args:
            reason: Short category, e.g. "customer_requested_human" or "out_of_scope".
            summary: A concise handover summary of the conversation so far: who the
                caller is (if verified), what they wanted, and what was already done
                or attempted, so they do not have to repeat themselves.
        """
        userdata = context.userdata
        try:
            ticket = await userdata.bank.create_escalation(
                reason=reason, summary=summary, customer_id=userdata.customer_id
            )
        except BankAPIError as exc:
            raise ToolError(
                "The escalation system is unavailable. Apologise and suggest the "
                "customer call the contact centre directly or visit a branch."
            ) from exc
        userdata.escalated = True
        userdata.escalation_ref = ticket.ticket_ref
        await userdata.emitter.emit(
            ToolEvent(
                type="escalation",
                result_summary=(
                    f"Escalated to a human consultant. Ticket {ticket.ticket_ref}. "
                    f"Reason: {reason}. Handover summary: {summary}"
                ),
            )
        )
        return (
            f"Escalation logged with reference {ticket.ticket_ref}. Tell the caller a "
            "consultant will assist them shortly, read the reference number slowly, "
            "and close the call politely."
        )
