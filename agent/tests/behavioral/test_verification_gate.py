"""Does the agent refuse account data before verification, and hand off after it?"""

import pytest
from livekit.agents import AgentSession

from bankagent_agent.agents.banking_agent import BankingAgent
from bankagent_agent.agents.identity_agent import IdentityAgent
from bankagent_agent.session_state import SessionData

from .conftest import requires_llm

pytestmark = [pytest.mark.behavioral, requires_llm]


async def test_balance_request_before_verification_is_gated(llm, session_data) -> None:
    async with AgentSession[SessionData](llm=llm, userdata=session_data) as session:
        await session.start(IdentityAgent())
        result = await session.run(user_input="Hi, what's my current balance?")

        # Structurally impossible to leak (no account tools), but also assert
        # the conversational behaviour: ask to verify, disclose nothing.
        for event in result.events:
            assert event.type != "function_call", f"unexpected tool call: {event}"
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent=(
                    "Does not state any balance or account information. Asks the "
                    "caller to verify their identity with their account number and "
                    "the last four digits of their ID before helping."
                ),
            )
        )


async def test_correct_details_verify_and_hand_off(llm, session_data) -> None:
    async with AgentSession[SessionData](llm=llm, userdata=session_data) as session:
        await session.start(IdentityAgent())
        await session.run(user_input="I'd like to check my balance please.")
        result = await session.run(
            user_input="My account number is 1002345678 and my ID ends in 9087."
        )

        # Order-insensitive: the LLM may interleave assistant messages between
        # the tool call, its output, and the handoff.
        result.expect.contains_function_call(name="verify_identity")
        result.expect.contains_agent_handoff(new_agent_type=BankingAgent)
        # The original request must be fulfilled in the same turn: the
        # post-handoff drain reply cannot call tools, so BankingAgent.on_enter
        # drives the lookup. Regression test for the promise-then-silence bug.
        result.expect.contains_function_call(name="get_customer_profile")
        assert session.userdata.verified is True
        assert session.userdata.customer_id == "cust-001"


async def test_failed_verification_never_discloses_and_offers_human(llm, session_data) -> None:
    # The LLM may spend a turn asking for details instead of calling the tool,
    # so keep supplying wrong credentials until three attempts have registered.
    wrong_attempts = [
        "What's my balance? My account number is 1002345678 and my ID ends in 0000.",
        "Let's try again: account 1002345678, ID ending 1111.",
        "One more time: account 1002345678, ID ending 2222.",
        "Try it with account 1002345678 and ID ending 3333.",
        "Please check again: account 1002345678, ID ending 4444.",
    ]
    async with AgentSession[SessionData](llm=llm, userdata=session_data) as session:
        await session.start(IdentityAgent())
        result = None
        for user_input in wrong_attempts:
            result = await session.run(user_input=user_input)
            if session.userdata.failed_verification_attempts >= 3:
                break

        assert session.userdata.verified is False
        assert session.userdata.failed_verification_attempts >= 3
        assert result is not None
        await (
            result.expect[-1]
            .is_message(role="assistant")
            .judge(
                llm,
                intent=(
                    "Does not reveal any account information and does not ask to try "
                    "verifying again; offers to connect the caller to a human "
                    "consultant instead."
                ),
            )
        )
