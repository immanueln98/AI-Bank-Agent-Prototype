"""Structural guarantees of the verification gate + decorator/schema interop.

These tests are the cheap, no-LLM assertion of the core safety claims:
1. The pre-verification agent has NO account tools (structural gate).
2. @emits_tool_events does not break LiveKit's tool-schema extraction.
3. With STEP_UP_ENABLED=false the step-up tools do not exist at all.
"""

import asyncio

from livekit.agents import ChatContext
from livekit.agents.llm import utils as llm_utils

from bankagent_agent.agents.banking_agent import STEP_UP_TOOL_NAMES, BankingAgent
from bankagent_agent.agents.identity_agent import IdentityAgent

ACCOUNT_TOOLS = {
    "get_customer_profile",
    "get_recent_transactions",
    "report_card_lost",
    "dispute_transaction",
    "send_step_up_code",
    "verify_step_up_code",
}


def _tool_schemas(agent) -> dict[str, dict]:
    schemas = {}
    for tool in agent.tools:
        schema = llm_utils.build_legacy_openai_schema(tool, internally_tagged=True)
        schemas[schema["name"]] = schema
    return schemas


def _banking_agent() -> BankingAgent:
    return BankingAgent(chat_ctx=ChatContext(), first_name="Thabo", account_masked="****5678")


def test_identity_agent_has_no_account_tools() -> None:
    tools = set(_tool_schemas(IdentityAgent()))
    assert tools == {"verify_identity", "search_faq", "escalate_to_human"}
    assert not tools & ACCOUNT_TOOLS


def test_banking_agent_has_full_toolset() -> None:
    tools = set(_tool_schemas(_banking_agent()))
    assert tools >= ACCOUNT_TOOLS
    assert {"search_faq", "escalate_to_human"} <= tools
    assert "verify_identity" not in tools  # no re-verification loops post-handoff


def test_no_agent_has_money_movement_tools() -> None:
    all_tools = set(_tool_schemas(IdentityAgent())) | set(_tool_schemas(_banking_agent()))
    for forbidden in ("transfer", "payment", "pay", "debit_order"):
        assert not any(forbidden in name for name in all_tools)


def test_decorated_tools_expose_llm_visible_parameters() -> None:
    schemas = _tool_schemas(_banking_agent())

    verify_params = schemas["report_card_lost"]["parameters"]
    assert verify_params["required"] == ["card_last4"]
    assert "last four digits" in verify_params["properties"]["card_last4"]["description"]

    txn_params = schemas["get_recent_transactions"]["parameters"]
    assert txn_params["properties"]["limit"]["default"] == 10

    # RunContext/self must never leak into the LLM-visible schema.
    for schema in schemas.values():
        assert "context" not in schema["parameters"]["properties"]
        assert "self" not in schema["parameters"]["properties"]


def test_tool_descriptions_present() -> None:
    for name, schema in _tool_schemas(IdentityAgent()).items():
        assert schema["description"], f"{name} has no description"


def test_step_up_disabled_removes_the_tools_entirely() -> None:
    """STEP_UP_ENABLED=false is structural, not prompt-level: after on_enter's
    filter runs, the step-up tools do not exist for the LLM to call."""
    agent = BankingAgent(
        chat_ctx=ChatContext(),
        first_name="Thabo",
        account_masked="****5678",
        step_up_mode="off",
    )
    asyncio.run(agent.remove_step_up_tools_if_disabled())
    tools = set(_tool_schemas(agent))
    assert not tools & STEP_UP_TOOL_NAMES
    assert {"report_card_lost", "dispute_transaction", "get_customer_profile"} <= tools


def test_step_up_enabled_keeps_the_tools() -> None:
    agent = _banking_agent()
    asyncio.run(agent.remove_step_up_tools_if_disabled())  # no-op when enabled
    assert set(_tool_schemas(agent)) >= STEP_UP_TOOL_NAMES


def test_action_tools_declare_step_up_requirement() -> None:
    """The LLM-visible descriptions must state the step-up requirement so the
    model runs the flow proactively; _require_step_up is the structural backstop."""
    schemas = _tool_schemas(_banking_agent())
    for action in ("report_card_lost", "dispute_transaction"):
        assert "step-up" in schemas[action]["description"].lower()
