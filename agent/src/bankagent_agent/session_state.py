"""Per-call shared state, carried on AgentSession.userdata.

Both agents (pre- and post-verification) and every tool read/write this via
``context.userdata``. The ``verified`` flag is the defense-in-depth guard;
the primary gate is structural (the pre-verification agent has no account
tools at all - see agents/identity_agent.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from bankagent_shared import KnownPII

from .bank_client import BankClient
from .events import ToolEventEmitter


@dataclass
class SessionData:
    bank: BankClient
    emitter: ToolEventEmitter
    known_pii: KnownPII
    session_id: str = field(default_factory=lambda: uuid4().hex[:12])
    room_name: str = ""
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    verified: bool = False
    customer_id: str | None = None
    customer_first_name: str | None = None
    account_masked: str | None = None  # e.g. "****5678"
    failed_verification_attempts: int = 0
    locked_out: bool = False  # 3 failed verifications this call

    # Possession-factor step-up (one-time code to the registered banking app):
    # required for account ACTIONS (card block, dispute); reads need tier 1 only.
    # step_up_enabled mirrors AgentSettings.step_up_enabled (STEP_UP_ENABLED):
    # when False the step-up tools are removed and actions need tier 1 only.
    step_up_enabled: bool = True
    step_up_verified: bool = False
    failed_step_up_attempts: int = 0
    step_up_locked: bool = False  # 3 failed codes this call - actions human-only

    escalated: bool = False
    escalation_ref: str | None = None
