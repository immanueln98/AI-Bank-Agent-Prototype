"""Step-up verification: one-time approval codes to the registered device.

Why this factor: account number + ID digits + any spoken passphrase are all
"something you know" - NIST 800-63B is explicit that two knowledge factors do
not make multi-factor authentication, and a leaked dossier defeats them all at
once. A code delivered to the registered banking app is "something you have",
and app delivery (vs SMS) sidesteps SIM-swap fraud - the dominant OTP attack
in South Africa. The agent requires it before any account ACTION (card block,
dispute); reads need tier-1 verification only.

PRODUCTION NOTE: this is where the bank's real push-notification / in-app
approval service plugs in (e.g. the same rails as FNB-style in-app approvals).
The demo simulates delivery: the console's "customer phone" panel polls the
demo-only endpoint in demo.py. Codes are single-use, per-code attempt-limited,
and never returned by the non-demo API surface.
"""

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import APIRouter

from bankagent_shared import get_logger
from bankagent_shared.models import StepUpSendResult, StepUpVerifyRequest, StepUpVerifyResult

from .customers import get_customer_or_404

router = APIRouter()
log = get_logger(__name__)

MAX_ATTEMPTS_PER_CODE = 3


@dataclass
class _Challenge:
    customer_id: str
    customer_first_name: str
    code: str
    sent_at: str
    attempts_used: int = 0
    consumed: bool = False

    @property
    def alive(self) -> bool:
        return not self.consumed and self.attempts_used < MAX_ATTEMPTS_PER_CODE


# In-memory, newest-last (resets on restart, like all POC state). The last
# entry doubles as "what the customer's phone currently shows" for the demo.
_challenges: list[_Challenge] = []


def latest_challenge() -> _Challenge | None:
    """Read by the demo-only router; not part of the bank-API surface."""
    return _challenges[-1] if _challenges else None


def reset_stepup() -> None:
    """Restore the empty store. Used by tests."""
    _challenges.clear()


def _current_for(customer_id: str) -> _Challenge | None:
    for challenge in reversed(_challenges):
        if challenge.customer_id == customer_id:
            return challenge
    return None


@router.post("/customers/{customer_id}/stepup/send", response_model=StepUpSendResult)
def send_step_up_code(customer_id: str) -> StepUpSendResult:
    record = get_customer_or_404(customer_id)
    code = f"{secrets.randbelow(1_000_000):06d}"
    _challenges.append(
        _Challenge(
            customer_id=customer_id,
            customer_first_name=record.profile.first_name,
            code=code,
            sent_at=datetime.now(UTC).isoformat(timespec="seconds"),
        )
    )
    log.info("stepup_code_sent", customer_id=customer_id, device=record.device_masked)
    return StepUpSendResult(sent_to=record.device_masked)


@router.post("/customers/{customer_id}/stepup/verify", response_model=StepUpVerifyResult)
def verify_step_up_code(customer_id: str, req: StepUpVerifyRequest) -> StepUpVerifyResult:
    get_customer_or_404(customer_id)
    challenge = _current_for(customer_id)
    if challenge is None or not challenge.alive:
        # No live code: treat as a failed attempt with nothing left on it.
        log.info("stepup_verify_no_live_code", customer_id=customer_id)
        return StepUpVerifyResult(verified=False, attempts_remaining=0)

    challenge.attempts_used += 1
    supplied = req.code.strip().replace(" ", "")
    if secrets.compare_digest(supplied, challenge.code):
        challenge.consumed = True  # single-use
        log.info("stepup_verified", customer_id=customer_id)
        return StepUpVerifyResult(verified=True, attempts_remaining=0)

    remaining = MAX_ATTEMPTS_PER_CODE - challenge.attempts_used
    log.info("stepup_verify_failed", customer_id=customer_id, attempts_remaining=remaining)
    return StepUpVerifyResult(verified=False, attempts_remaining=remaining)
