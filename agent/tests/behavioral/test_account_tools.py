"""Post-verification: does the agent ground its answers in tool calls?"""

import pytest
from livekit.agents import AgentSession, ChatContext

from bankagent_agent.agents.banking_agent import BankingAgent
from bankagent_agent.session_state import SessionData

from .conftest import requires_llm

pytestmark = [pytest.mark.behavioral, requires_llm]


def _banking_agent() -> BankingAgent:
    return BankingAgent(chat_ctx=ChatContext(), first_name="Thabo", account_masked="****5678")


async def test_balance_question_calls_profile_tool(llm, verified_session_data) -> None:
    async with AgentSession[SessionData](llm=llm, userdata=verified_session_data) as session:
        await session.start(_banking_agent())
        result = await session.run(user_input="How much money do I have in my cheque account?")

        result.expect.contains_function_call(name="get_customer_profile")
        await (
            result.expect[-1]
            .is_message(role="assistant")
            .judge(
                llm,
                intent=(
                    "States the cheque account balance of about eighteen thousand "
                    "four hundred and fifty two rand, taken from the tool result."
                ),
            )
        )


async def test_salary_question_calls_transactions_tool(llm, verified_session_data) -> None:
    async with AgentSession[SessionData](llm=llm, userdata=verified_session_data) as session:
        await session.start(_banking_agent())
        result = await session.run(user_input="Has my salary come in yet?")

        result.expect.contains_function_call(name="get_recent_transactions")
        await (
            result.expect[-1]
            .is_message(role="assistant")
            .judge(
                llm,
                intent="Confirms the salary from ACME Engineering has arrived, based on "
                "the transaction list.",
            )
        )


async def test_lost_card_flow_calls_action_tool(llm, verified_session_data) -> None:
    async with AgentSession[SessionData](llm=llm, userdata=verified_session_data) as session:
        await session.start(_banking_agent())
        await session.run(user_input="I've lost my card, please block it.")
        result = await session.run(user_input="Yes, it's the card ending 4821. Block it.")

        result.expect.contains_function_call(name="report_card_lost")
        await (
            result.expect[-1]
            .is_message(role="assistant")
            .judge(
                llm,
                intent="Confirms the card is blocked and mentions the replacement "
                "timeline or reference from the tool result.",
            )
        )
