"""API models shared by the mock bank backend (responses) and the voice agent
(HTTP-client parsing). Sharing one set of Pydantic classes means a schema change
breaks tests at build time instead of the demo at pitch time.

In a real integration these models would be generated from (or replaced by)
the bank's core-banking API contract.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from .events import ToolEvent

AccountType = Literal["cheque", "savings", "credit"]
TransactionStatus = Literal["posted", "pending", "flagged"]
CardStatus = Literal["active", "blocked"]


class Account(BaseModel):
    account_id: str
    account_masked: str  # e.g. "****5678" - full numbers never leave the backend
    type: AccountType
    currency: str  # ISO 4217: ZAR / BWP
    balance: float
    credit_limit: float | None = None
    available_credit: float | None = None


class CardInfo(BaseModel):
    last4: str
    status: CardStatus


class CustomerProfile(BaseModel):
    customer_id: str
    full_name: str
    first_name: str
    accounts: list[Account]
    card: CardInfo | None = None
    flags: list[str] = Field(default_factory=list)  # e.g. "unusual_activity_review"


class Transaction(BaseModel):
    transaction_id: str
    ts: date
    merchant: str
    description: str
    amount: float  # negative = money out
    currency: str
    status: TransactionStatus


class VerificationRequest(BaseModel):
    account_number: str
    id_last4: str


class VerificationResult(BaseModel):
    verified: bool
    customer_id: str | None = None
    first_name: str | None = None


class CardLostRequest(BaseModel):
    card_last4: str


class CardActionResult(BaseModel):
    card_last4: str
    status: CardStatus
    replacement_eta_days: int
    reference: str


class DisputeRequest(BaseModel):
    transaction_id: str
    reason: str


class DisputeResult(BaseModel):
    dispute_id: str
    transaction_id: str
    status: Literal["under_review"]
    sla_days: int


class FaqResult(BaseModel):
    question: str
    answer: str
    score: float


class EscalationRequest(BaseModel):
    customer_id: str | None = None
    reason: str
    summary: str


class EscalationTicket(BaseModel):
    ticket_ref: str
    queue: str


class TokenRequest(BaseModel):
    scenario: str | None = None
    participant_name: str | None = None


class TokenResponse(BaseModel):
    url: str
    token: str
    room: str


CallOutcome = Literal["contained", "escalated", "verification_failed", "abandoned"]


class CallRecord(BaseModel):
    """End-of-call operational record the agent posts to the backend.

    Everything in here is already PII-masked (events pass through the same
    redaction pipeline as the live activity feed) - it is safe to show on the
    supervisor dashboard and to retain as an audit trail.
    """

    session_id: str
    room: str
    scenario: str | None = None  # parsed from demo room names ("demo-<id>-…")
    started_at: str  # ISO 8601, UTC
    ended_at: str
    duration_seconds: float
    outcome: CallOutcome
    verified: bool
    customer_first_name: str | None = None
    account_masked: str | None = None
    failed_verification_attempts: int = 0
    locked_out: bool = False  # 3 failed verifications - a security event
    escalated: bool = False
    escalation_ref: str | None = None
    tools_used: list[str] = Field(default_factory=list)  # unique, first-use order
    tool_calls: int = 0
    tool_failures: int = 0
    events: list[ToolEvent] = Field(default_factory=list)  # masked audit trail
    usage_summary: str | None = None  # LLM/STT/TTS usage for cost tracking


class CallMetrics(BaseModel):
    """Aggregate KPIs over all stored call records - the dashboard tiles."""

    total_calls: int = 0
    contained: int = 0
    escalated: int = 0
    verification_failed: int = 0
    abandoned: int = 0
    lockouts: int = 0
    containment_rate: float | None = None  # contained / total, None until data
    avg_duration_seconds: float | None = None
    avg_tool_calls: float | None = None


class ScenarioInfo(BaseModel):
    """Demo cheat-sheet entry for the frontend scenario picker.

    Deliberately includes the fixture account number / ID digits: this is the
    presenter's crib card, not customer data.
    """

    id: str
    title: str
    customer_name: str
    account_number: str
    id_last4: str
    description: str
    suggested_lines: list[str]
