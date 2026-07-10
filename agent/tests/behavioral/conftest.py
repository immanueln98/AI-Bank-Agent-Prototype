"""Fixtures for agent-behavior tests (LiveKit test harness + a live LLM).

These tests need model credentials:
  - LLM_PROVIDER=inference (default): LIVEKIT_URL / LIVEKIT_API_KEY / LIVEKIT_API_SECRET
  - LLM_PROVIDER=anthropic: ANTHROPIC_API_KEY
They skip cleanly when credentials are absent, and are excluded from the
default `make test` run (marker: behavioral). Run with `make test-behavioral`.

The bank backend is NOT involved: tools run for real against StubBankClient
(canned fixture data), so the tests exercise LLM behaviour - tool choice,
verification gating, refusals - not HTTP.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

import pytest

from bankagent_agent.bank_client import BankAPIError
from bankagent_agent.config import AgentSettings, build_llm
from bankagent_agent.events import ToolEventEmitter
from bankagent_agent.session_state import SessionData
from bankagent_shared import KnownPII
from bankagent_shared.models import (
    Account,
    CardActionResult,
    CardInfo,
    CustomerProfile,
    DisputeResult,
    EscalationTicket,
    FaqResult,
    StepUpSendResult,
    StepUpVerifyResult,
    Transaction,
    VerificationResult,
)


def _has_credentials() -> bool:
    settings = AgentSettings()
    if settings.llm_provider == "anthropic":
        return settings.anthropic_api_key is not None or bool(os.environ.get("ANTHROPIC_API_KEY"))
    return bool(settings.livekit_api_key and settings.livekit_api_secret)


pytestmark = pytest.mark.behavioral

requires_llm = pytest.mark.skipif(
    not _has_credentials(),
    reason="behavioral tests need LLM credentials (LIVEKIT_* or ANTHROPIC_API_KEY)",
)


THABO_PROFILE = CustomerProfile(
    customer_id="cust-001",
    full_name="Thabo Mokoena",
    first_name="Thabo",
    accounts=[
        Account(
            account_id="acc-001-chq",
            account_masked="****5678",
            type="cheque",
            currency="ZAR",
            balance=18452.75,
        ),
    ],
    card=CardInfo(last4="4821", status="active"),
)

THABO_TRANSACTIONS = [
    Transaction(
        transaction_id="txn-001-010",
        ts="2026-07-03",  # type: ignore[arg-type]
        merchant="ACME Engineering",
        description="SALARY - ACME ENGINEERING (PTY) LTD",
        amount=28500.00,
        currency="ZAR",
        status="posted",
    ),
    Transaction(
        transaction_id="txn-001-009",
        ts="2026-07-03",  # type: ignore[arg-type]
        merchant="Checkers Sixty60",
        description="Groceries delivery",
        amount=-1240.50,
        currency="ZAR",
        status="posted",
    ),
]


STUB_STEP_UP_CODE = "482913"


@dataclass
class StubBankClient:
    """In-memory stand-in for BankClient with Thabo's fixture data."""

    verify_calls: list[tuple[str, str]] = field(default_factory=list)
    step_up_sends: int = 0

    async def send_step_up(self, customer_id: str) -> StepUpSendResult:
        self.step_up_sends += 1
        return StepUpSendResult(sent_to="the Meridian app on your registered phone")

    async def verify_step_up(self, customer_id: str, code: str) -> StepUpVerifyResult:
        ok = code.strip().replace(" ", "") == STUB_STEP_UP_CODE
        return StepUpVerifyResult(verified=ok, attempts_remaining=0 if ok else 2)

    async def verify(self, account_number: str, id_last4: str) -> VerificationResult:
        self.verify_calls.append((account_number, id_last4))
        if account_number.replace(" ", "") == "1002345678" and id_last4 == "9087":
            return VerificationResult(verified=True, customer_id="cust-001", first_name="Thabo")
        if account_number.replace(" ", "") == "9999999999":
            raise BankAPIError(404, "Unknown account number")
        return VerificationResult(verified=False)

    async def get_customer_profile(self, customer_id: str) -> CustomerProfile:
        return THABO_PROFILE

    async def get_recent_transactions(self, customer_id: str, limit: int = 10) -> list[Transaction]:
        return THABO_TRANSACTIONS[:limit]

    async def report_card_lost(self, customer_id: str, card_last4: str) -> CardActionResult:
        if card_last4 != "4821":
            raise BankAPIError(404, "No matching card on this profile")
        return CardActionResult(
            card_last4="4821", status="blocked", replacement_eta_days=5, reference="CARD-TEST01"
        )

    async def dispute_transaction(
        self, customer_id: str, transaction_id: str, reason: str
    ) -> DisputeResult:
        return DisputeResult(
            dispute_id="DSP-TEST01",
            transaction_id=transaction_id,
            status="under_review",
            sla_days=10,
        )

    async def search_faq(self, query: str) -> list[FaqResult]:
        return [
            FaqResult(
                question="What are your branch operating hours?",
                answer="Branches are open weekdays 08:30-16:00 and Saturdays 08:30-12:00.",
                score=1.0,
            )
        ]

    async def create_escalation(
        self, reason: str, summary: str, customer_id: str | None = None
    ) -> EscalationTicket:
        return EscalationTicket(ticket_ref="ESC-20260706-042", queue="general-support")


def make_session_data() -> SessionData:
    known = KnownPII()
    return SessionData(
        bank=StubBankClient(),  # type: ignore[arg-type]
        emitter=ToolEventEmitter(known),
        known_pii=known,
    )


@pytest.fixture
def session_data() -> SessionData:
    return make_session_data()


@pytest.fixture
def verified_session_data() -> SessionData:
    data = make_session_data()
    data.verified = True
    data.customer_id = "cust-001"
    data.customer_first_name = "Thabo"
    data.account_masked = "****5678"
    return data


@pytest.fixture
def llm():
    return build_llm(AgentSettings())
