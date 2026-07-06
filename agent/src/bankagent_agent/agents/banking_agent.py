"""Post-verification agent: the only place account tools exist.

Instantiated exclusively by IdentityAgent.verify_identity on success, with the
conversation history carried over. Every tool still re-checks
``userdata.verified`` (defense in depth against future refactors); the
primary guarantee is that the pre-verification agent simply does not have
these tools at all.
"""

from __future__ import annotations

from typing import Any

from livekit.agents import Agent, ChatContext, RunContext, function_tool
from livekit.agents.llm import ToolError

from ..bank_client import BankAPIError
from ..instrumentation import emits_tool_events
from ..session_state import SessionData
from .prompts import BANKING_INSTRUCTIONS
from .support_tools import FALLBACK_LINE, SupportToolsMixin


def _require_verified(context: RunContext[SessionData]) -> str:
    """Returns the verified customer_id or refuses the call."""
    userdata = context.userdata
    if not userdata.verified or userdata.customer_id is None:
        raise ToolError(
            "The caller is not identity-verified. Do not disclose any account "
            "information. Ask them to verify their identity first."
        )
    return userdata.customer_id


class BankingAgent(SupportToolsMixin, Agent):
    def __init__(self, *, chat_ctx: ChatContext, first_name: str, account_masked: str) -> None:
        super().__init__(
            instructions=BANKING_INSTRUCTIONS.format(
                first_name=first_name, account_masked=account_masked
            ),
            chat_ctx=chat_ctx,
        )

    async def on_enter(self) -> None:
        # The reply that accompanies the verify_identity handoff is generated
        # with tools disabled (the framework drains the old activity), so it
        # can only announce what comes next. This fresh generation is what
        # actually fulfils the caller's original request - without it the
        # agent promises to check and then falls silent.
        self.session.generate_reply(
            instructions=(
                "Continue with the caller's original request now. If it needs "
                "account data, call the matching tool first and answer from "
                "its result. Do not introduce yourself again."
            )
        )

    @function_tool()
    @emits_tool_events
    async def get_customer_profile(self, context: RunContext[SessionData]) -> dict[str, Any]:
        """Fetch the verified customer's profile: accounts with balances, card
        status, and any account flags. Use for balance and account questions."""
        customer_id = _require_verified(context)
        try:
            profile = await context.userdata.bank.get_customer_profile(customer_id)
        except BankAPIError as exc:
            raise ToolError(FALLBACK_LINE) from exc
        return profile.model_dump(mode="json")

    @function_tool()
    @emits_tool_events
    async def get_recent_transactions(
        self, context: RunContext[SessionData], limit: int = 10
    ) -> list[dict[str, Any]]:
        """Fetch the verified customer's most recent transactions, newest first.
        Use for questions like "did my salary come in" or "what was that charge".

        Args:
            limit: How many transactions to fetch (1-50).
        """
        customer_id = _require_verified(context)
        try:
            transactions = await context.userdata.bank.get_recent_transactions(
                customer_id, limit=max(1, min(limit, 50))
            )
        except BankAPIError as exc:
            raise ToolError(FALLBACK_LINE) from exc
        return [t.model_dump(mode="json") for t in transactions]

    @function_tool()
    @emits_tool_events
    async def report_card_lost(
        self, context: RunContext[SessionData], card_last4: str
    ) -> dict[str, Any]:
        """Block the customer's card after they report it lost or stolen, and order
        a replacement. Confirm the last four digits of the card with the customer
        before calling this.

        Args:
            card_last4: The last four digits of the card to block.
        """
        customer_id = _require_verified(context)
        try:
            result = await context.userdata.bank.report_card_lost(customer_id, card_last4)
        except BankAPIError as exc:
            if exc.status_code == 404:
                raise ToolError(
                    "No card with those digits exists on this profile. Re-confirm the "
                    "last four digits with the customer."
                ) from exc
            if exc.status_code == 409:
                raise ToolError(
                    "That card is already blocked. Reassure the customer it cannot be "
                    "used and that the earlier block stands."
                ) from exc
            raise ToolError(FALLBACK_LINE) from exc
        return result.model_dump(mode="json")

    @function_tool()
    @emits_tool_events
    async def dispute_transaction(
        self, context: RunContext[SessionData], transaction_id: str, reason: str
    ) -> dict[str, Any]:
        """Open a dispute on a transaction the customer does not recognise or did
        not authorise. Look the transaction up with get_recent_transactions first
        and confirm it with the customer before disputing.

        Args:
            transaction_id: The id of the transaction being disputed.
            reason: The customer's reason, in one sentence.
        """
        customer_id = _require_verified(context)
        try:
            result = await context.userdata.bank.dispute_transaction(
                customer_id, transaction_id, reason
            )
        except BankAPIError as exc:
            if exc.status_code == 404:
                raise ToolError(
                    "That transaction id was not found on this account. Fetch recent "
                    "transactions again and confirm which one the customer means."
                ) from exc
            if exc.status_code == 409:
                raise ToolError(
                    "A dispute already exists for that transaction. Reassure the "
                    "customer it is being reviewed."
                ) from exc
            raise ToolError(FALLBACK_LINE) from exc
        return result.model_dump(mode="json")
