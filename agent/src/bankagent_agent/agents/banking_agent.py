"""Post-verification agent: the only place account tools exist.

Instantiated exclusively by IdentityAgent.verify_identity on success, with the
conversation history carried over. Every tool still re-checks
``userdata.verified`` (defense in depth against future refactors); the
primary guarantee is that the pre-verification agent simply does not have
these tools at all.

Tiered authentication: tier-1 verification (account + ID digits) unlocks
READ tools only. Account ACTIONS (card block, dispute) additionally require
possession-factor step-up - a one-time code sent to the registered banking
app - enforced in code by ``_require_step_up``, not just by prompt.
"""

from __future__ import annotations

from typing import Any

from livekit.agents import Agent, ChatContext, RunContext, function_tool
from livekit.agents.llm import ToolError

from bankagent_shared import ToolEvent

from ..bank_client import BankAPIError
from ..instrumentation import emits_tool_events
from ..session_state import SessionData
from .prompts import banking_instructions
from .support_tools import FALLBACK_LINE, SupportToolsMixin

MAX_STEP_UP_ATTEMPTS = 3
STEP_UP_TOOL_NAMES = {"send_step_up_code", "verify_step_up_code"}


def _require_verified(context: RunContext[SessionData]) -> str:
    """Returns the verified customer_id or refuses the call."""
    userdata = context.userdata
    if not userdata.verified or userdata.customer_id is None:
        raise ToolError(
            "The caller is not identity-verified. Do not disclose any account "
            "information. Ask them to verify their identity first."
        )
    return userdata.customer_id


def _require_step_up(context: RunContext[SessionData]) -> str:
    """Account actions need the possession factor on top of tier-1 identity.

    With STEP_UP_ENABLED=false the gate degrades to tier-1 only (the demo's
    original single-tier flow, kept toggleable for A/B pitching).
    """
    customer_id = _require_verified(context)
    userdata = context.userdata
    if not userdata.step_up_enabled:
        return customer_id
    if userdata.step_up_locked:
        raise ToolError(
            "Step-up verification is locked for this call after repeated failed "
            "codes. Do not attempt this action again. Offer a human consultant."
        )
    if not userdata.step_up_verified:
        raise ToolError(
            "This action changes the customer's account and needs step-up "
            "verification first. Call send_step_up_code, ask the customer to "
            "read back the six-digit code from their Meridian app, verify it "
            "with verify_step_up_code, then retry this action."
        )
    return customer_id


class BankingAgent(SupportToolsMixin, Agent):
    def __init__(
        self,
        *,
        chat_ctx: ChatContext,
        first_name: str,
        account_masked: str,
        step_up_enabled: bool = True,
    ) -> None:
        self._step_up_enabled = step_up_enabled
        super().__init__(
            instructions=banking_instructions(step_up_enabled).format(
                first_name=first_name, account_masked=account_masked
            ),
            chat_ctx=chat_ctx,
        )

    async def remove_step_up_tools_if_disabled(self) -> None:
        """With step-up disabled the tools are removed entirely - the LLM
        cannot call what does not exist (same structural principle as the
        identity gate). Public so tests can assert the structure directly."""
        if self._step_up_enabled:
            return

        def name_of(tool: object) -> str | None:
            return getattr(getattr(tool, "info", None), "name", None)

        await self.update_tools([t for t in self.tools if name_of(t) not in STEP_UP_TOOL_NAMES])

    async def on_enter(self) -> None:
        await self.remove_step_up_tools_if_disabled()
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
    async def send_step_up_code(self, context: RunContext[SessionData]) -> str:
        """Send a one-time six-digit approval code to the Meridian app on the
        customer's registered device. Required before any account action (card
        block, dispute). Call this once, then ask the customer to open their
        Meridian app and read the code back to you."""
        customer_id = _require_verified(context)
        userdata = context.userdata
        if not userdata.step_up_enabled:  # backstop; the tool is normally removed
            raise ToolError("Step-up is disabled in this deployment. Perform the action directly.")
        if userdata.step_up_locked:
            raise ToolError(
                "Step-up is locked for this call after repeated failed codes. Do "
                "not send another code. Offer a human consultant instead."
            )
        try:
            result = await userdata.bank.send_step_up(customer_id)
        except BankAPIError as exc:
            raise ToolError(FALLBACK_LINE) from exc
        return (
            f"A one-time approval code was sent to {result.sent_to}. Ask the "
            "customer to open the app and read the six-digit code back, then "
            "call verify_step_up_code with it."
        )

    @function_tool()
    @emits_tool_events
    async def verify_step_up_code(self, context: RunContext[SessionData], code: str) -> str:
        """Check the six-digit approval code the customer read back from their
        Meridian app. On success, account actions unlock for this call.

        Args:
            code: The six-digit code the customer read out, digits only.
        """
        customer_id = _require_verified(context)
        userdata = context.userdata
        if not userdata.step_up_enabled:  # backstop; the tool is normally removed
            raise ToolError("Step-up is disabled in this deployment. Perform the action directly.")
        if userdata.step_up_locked:
            raise ToolError(
                "Step-up is locked for this call. Do not try more codes. Offer a "
                "human consultant instead."
            )
        try:
            result = await userdata.bank.verify_step_up(customer_id, code)
        except BankAPIError as exc:
            raise ToolError(FALLBACK_LINE) from exc

        if result.verified:
            userdata.step_up_verified = True
            await userdata.emitter.emit(
                ToolEvent(
                    type="step_up_verified",
                    result_summary="Step-up verified: one-time code from the "
                    "customer's registered device confirmed.",
                )
            )
            return (
                "Step-up verified. You may now perform the account action the customer asked for."
            )

        userdata.failed_step_up_attempts += 1
        if userdata.failed_step_up_attempts >= MAX_STEP_UP_ATTEMPTS:
            userdata.step_up_locked = True
            await userdata.emitter.emit(
                ToolEvent(
                    type="security_lockout",
                    result_summary=f"{MAX_STEP_UP_ATTEMPTS} failed step-up codes - "
                    "account actions locked for this call; human handoff only. "
                    "Balance and transaction questions remain available.",
                )
            )
            return (
                "That code is not correct, and step-up has now failed three "
                "times. Do NOT send or check more codes. The customer can still "
                "ask about balances and transactions, but for any account "
                "changes offer a human consultant."
            )
        return (
            "That code is not correct. Ask the customer to double-check the "
            "newest code in their Meridian app and read it again. If they never "
            "received it, send a fresh one with send_step_up_code."
        )

    @function_tool()
    @emits_tool_events
    async def report_card_lost(
        self, context: RunContext[SessionData], card_last4: str
    ) -> dict[str, Any]:
        """Block the customer's card after they report it lost or stolen, and order
        a replacement. Requires step-up verification first. Confirm the last four
        digits of the card with the customer before calling this.

        Args:
            card_last4: The last four digits of the card to block.
        """
        customer_id = _require_step_up(context)
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
        not authorise. Requires step-up verification first. Look the transaction
        up with get_recent_transactions first and confirm it with the customer
        before disputing.

        Args:
            transaction_id: The id of the transaction being disputed.
            reason: The customer's reason, in one sentence.
        """
        customer_id = _require_step_up(context)
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
