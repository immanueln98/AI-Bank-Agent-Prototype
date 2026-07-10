"""Pre-verification agent - the structural identity gate.

This agent has NO account-data tools, so no prompt injection or model
misbehaviour can leak account information before verification: the tools to
do so do not exist yet. Successful verification returns a
:class:`BankingAgent` handoff (with conversation history carried over), which
is the only way account tools ever enter the session.
"""

from __future__ import annotations

from livekit.agents import Agent, RunContext, function_tool
from livekit.agents.llm import ToolError

from bankagent_shared import ToolEvent, mask_account

from ..bank_client import BankAPIError
from ..instrumentation import emits_tool_events
from ..session_state import SessionData
from .banking_agent import BankingAgent
from .prompts import IDENTITY_INSTRUCTIONS, OPENING_GREETING
from .support_tools import SupportToolsMixin

MAX_VERIFICATION_ATTEMPTS = 3


class IdentityAgent(SupportToolsMixin, Agent):
    def __init__(self) -> None:
        super().__init__(instructions=IDENTITY_INSTRUCTIONS)

    async def on_enter(self) -> None:
        # Fixed text via say(), not generate_reply(): the caller hears the
        # mandated disclosure immediately (no LLM round-trip at call start)
        # and its wording is deterministic rather than LLM-best-effort.
        self.session.say(OPENING_GREETING)

    @function_tool()
    @emits_tool_events
    async def verify_identity(
        self, context: RunContext[SessionData], account_number: str, id_last4: str
    ) -> tuple[Agent, str] | str:
        """Verify the caller's identity with their account number and the last four
        digits of their ID or Omang number. Required before any account help.
        Collect both values from the caller before calling this.

        Args:
            account_number: The caller's account number, digits only.
            id_last4: The last four digits of the caller's ID/Omang number.
        """
        userdata = context.userdata
        # Register the raw digits so every log/transcript/event masks them.
        userdata.known_pii.add(account_number)

        try:
            result = await userdata.bank.verify(account_number, id_last4)
        except BankAPIError as exc:
            if exc.status_code == 404:
                result = None  # unknown account = failed attempt, not an outage
            else:
                raise ToolError(
                    "Verification is unavailable right now. Apologise and offer to "
                    "connect the customer to a consultant."
                ) from exc

        if result is None or not result.verified:
            userdata.failed_verification_attempts += 1
            if userdata.failed_verification_attempts >= MAX_VERIFICATION_ATTEMPTS:
                # First-class security signal: shows red in the activity panel
                # and lands in the call record for the supervisor dashboard.
                if not userdata.locked_out:
                    userdata.locked_out = True
                    await userdata.emitter.emit(
                        ToolEvent(
                            type="security_lockout",
                            result_summary=(
                                f"{MAX_VERIFICATION_ATTEMPTS} failed verification attempts - "
                                "account access locked for this call; human handoff only."
                            ),
                        )
                    )
                return (
                    "Verification failed three times. Do NOT attempt again. Offer to "
                    "connect the caller to a human consultant."
                )
            return (
                "Those details do not match our records. Do not reveal which detail "
                "is wrong. Ask the caller to double-check and try once more."
            )

        userdata.verified = True
        userdata.customer_id = result.customer_id
        userdata.customer_first_name = result.first_name
        userdata.account_masked = mask_account(account_number)
        await userdata.emitter.emit(
            ToolEvent(
                type="identity_verified",
                result_summary=f"Identity verified: {result.first_name} "
                f"({userdata.account_masked})",
            )
        )
        return (
            BankingAgent(
                chat_ctx=self.chat_ctx,
                first_name=result.first_name or "the customer",
                account_masked=userdata.account_masked,
                step_up_enabled=userdata.step_up_enabled,
            ),
            f"Identity verified for {result.first_name}. You may now help with their "
            "account. Greet them by name and continue with their original request.",
        )
