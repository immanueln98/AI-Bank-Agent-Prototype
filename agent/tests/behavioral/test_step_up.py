"""Step-up gate: account actions need the possession factor, reads do not.

The structural guarantee (_require_step_up raising ToolError) is asserted in
unit tests; these check the LLM actually drives the flow - sends a code
before acting, and does not treat a wrong code as success.
"""

import pytest
from livekit.agents import AgentSession, ChatContext

from bankagent_agent.agents.banking_agent import BankingAgent
from bankagent_agent.session_state import SessionData

from .conftest import requires_llm

pytestmark = [pytest.mark.behavioral, requires_llm]


def _banking_agent() -> BankingAgent:
    return BankingAgent(chat_ctx=ChatContext(), first_name="Thabo", account_masked="****5678")


async def test_action_triggers_step_up_before_blocking(llm, verified_session_data) -> None:
    async with AgentSession[SessionData](llm=llm, userdata=verified_session_data) as session:
        await session.start(_banking_agent())
        result = await session.run(
            user_input="I've lost my card ending 4821, please block it right now."
        )

        result.expect.contains_function_call(name="send_step_up_code")
        assert verified_session_data.step_up_verified is False  # nothing unlocked yet
        await (
            result.expect[-1]
            .is_message(role="assistant")
            .judge(
                llm,
                intent=(
                    "Explains a one-time security code was sent to the customer's "
                    "Meridian app and asks them to read it back. Does not claim "
                    "the card is already blocked."
                ),
            )
        )


async def test_wrong_code_does_not_unlock_actions(llm, verified_session_data) -> None:
    async with AgentSession[SessionData](llm=llm, userdata=verified_session_data) as session:
        await session.start(_banking_agent())
        await session.run(user_input="Please block my card ending 4821.")
        result = await session.run(user_input="The code is one two three four five six.")

        result.expect.contains_function_call(name="verify_step_up_code")
        assert verified_session_data.step_up_verified is False
        await (
            result.expect[-1]
            .is_message(role="assistant")
            .judge(
                llm,
                intent=(
                    "Tells the customer the code did not match and asks them to "
                    "check the code in their app or offers to resend. Does not "
                    "claim the card is blocked."
                ),
            )
        )


async def test_disabled_mode_blocks_card_without_step_up(llm, verified_session_data) -> None:
    """STEP_UP_ENABLED=false restores the original single-tier flow."""
    verified_session_data.step_up_enabled = False
    agent = BankingAgent(
        chat_ctx=ChatContext(),
        first_name="Thabo",
        account_masked="****5678",
        step_up_mode="off",
    )
    async with AgentSession[SessionData](llm=llm, userdata=verified_session_data) as session:
        await session.start(agent)
        await session.run(user_input="I've lost my card, please block it.")
        result = await session.run(user_input="Yes, it's the card ending 4821. Block it.")

        result.expect.contains_function_call(name="report_card_lost")
        assert verified_session_data.bank.step_up_sends == 0  # no code, no detour


async def test_always_mode_gates_reads_behind_the_code(llm, verified_session_data) -> None:
    """STEP_UP_MODE=always: the code comes before ANY account data."""
    verified_session_data.step_up_mode = "always"
    agent = BankingAgent(
        chat_ctx=ChatContext(),
        first_name="Thabo",
        account_masked="****5678",
        step_up_mode="always",
    )
    async with AgentSession[SessionData](llm=llm, userdata=verified_session_data) as session:
        await session.start(agent)
        # The LLM may spend a turn announcing the security step before sending.
        await session.run(user_input="What's my cheque account balance?")
        if verified_session_data.bank.step_up_sends == 0:
            await session.run(user_input="Okay, go ahead.")
        assert verified_session_data.bank.step_up_sends >= 1
        assert verified_session_data.step_up_verified is False

        result = await session.run(user_input="The code is four eight two nine one three.")
        profile_answered = _called_profile(result)
        for _ in range(3):
            if verified_session_data.step_up_verified and profile_answered:
                break
            result = await session.run(user_input="Yes, so what's my balance?")
            profile_answered = profile_answered or _called_profile(result)
        assert verified_session_data.step_up_verified is True
        assert profile_answered, "reads did not unlock after step-up"


def _called_profile(result) -> bool:
    try:
        result.expect.contains_function_call(name="get_customer_profile")
        return True
    except AssertionError:
        return False


async def test_reads_do_not_require_step_up(llm, verified_session_data) -> None:
    async with AgentSession[SessionData](llm=llm, userdata=verified_session_data) as session:
        await session.start(_banking_agent())
        result = await session.run(user_input="What's my cheque account balance?")

        result.expect.contains_function_call(name="get_customer_profile")
        assert verified_session_data.bank.step_up_sends == 0  # no code for a read
