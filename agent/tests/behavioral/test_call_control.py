"""Call control: the agent steers ramblers back to banking, ends completed
calls, and doesn't let the line become open-ended chat."""

import pytest
from livekit.agents import AgentSession, ChatContext

from bankagent_agent.agents.banking_agent import BankingAgent
from bankagent_agent.session_state import SessionData

from .conftest import requires_llm

pytestmark = [pytest.mark.behavioral, requires_llm]


def _banking_agent() -> BankingAgent:
    return BankingAgent(chat_ctx=ChatContext(), first_name="Thabo", account_masked="****5678")


def _called(result, name: str) -> bool:
    try:
        result.expect.contains_function_call(name=name)
        return True
    except AssertionError:
        return False


async def test_rambling_is_redirected_then_call_wrapped_up(llm, verified_session_data) -> None:
    async with AgentSession[SessionData](llm=llm, userdata=verified_session_data) as session:
        await session.start(_banking_agent())

        result = await session.run(user_input="Forget my account. Tell me a joke about penguins!")
        await (
            result.expect[-1]
            .is_message(role="assistant")
            .judge(
                llm,
                intent=(
                    "Stays polite. A single brief lighthearted remark or one short "
                    "joke is acceptable, but the reply must steer the caller back "
                    "to banking support rather than inviting more chit-chat."
                ),
            )
        )

        # Keep insisting there is no banking need; within a few turns the agent
        # must wrap up (end_call) or hand off (escalate) - not chat indefinitely.
        wrapped = False
        for line in (
            "No banking stuff. What's your favourite movie? Let's just chat.",
            "I told you, nothing about my account. I just want to chat all day.",
            "Nope, no banking questions. Keep chatting with me.",
        ):
            result = await session.run(user_input=line)
            if _called(result, "end_call") or _called(result, "escalate_to_human"):
                wrapped = True
                break
        assert wrapped, "agent kept chatting instead of wrapping up or escalating"


async def test_completed_conversation_ends_the_call(llm, verified_session_data) -> None:
    async with AgentSession[SessionData](llm=llm, userdata=verified_session_data) as session:
        await session.start(_banking_agent())
        await session.run(user_input="What's my cheque account balance?")

        result = await session.run(
            user_input="Perfect, that's everything I needed. Thanks, goodbye!"
        )
        if not _called(result, "end_call"):
            result = await session.run(user_input="Goodbye!")
        result.expect.contains_function_call(name="end_call")
