"""Identity verification, customer profile, and transaction history.

PRODUCTION NOTE: these handlers are the seam where a real bank plugs in its
core-banking / CIF APIs. The request/response contracts (bankagent_shared
.models) are what the voice agent depends on; keep those and swap the lookups.
"""

from fastapi import APIRouter, HTTPException, Query

from bankagent_shared import get_logger
from bankagent_shared.models import (
    CustomerProfile,
    Transaction,
    VerificationRequest,
    VerificationResult,
)

from ..fixtures import BY_ACCOUNT_NUMBER, CUSTOMERS, CustomerRecord

router = APIRouter()
log = get_logger(__name__)


def get_customer_or_404(customer_id: str) -> CustomerRecord:
    record = CUSTOMERS.get(customer_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Unknown customer")
    return record


@router.post("/verify", response_model=VerificationResult)
def verify_identity(req: VerificationRequest) -> VerificationResult:
    record = BY_ACCOUNT_NUMBER.get(req.account_number.strip().replace(" ", ""))
    if record is None:
        raise HTTPException(status_code=404, detail="Unknown account number")
    if record.id_last4 != req.id_last4.strip():
        log.info("verification_failed", customer_id=record.profile.customer_id)
        return VerificationResult(verified=False)
    log.info("verification_succeeded", customer_id=record.profile.customer_id)
    return VerificationResult(
        verified=True,
        customer_id=record.profile.customer_id,
        first_name=record.profile.first_name,
    )


@router.get("/customers/{customer_id}", response_model=CustomerProfile)
def get_customer_profile(customer_id: str) -> CustomerProfile:
    return get_customer_or_404(customer_id).profile


@router.get("/customers/{customer_id}/transactions", response_model=list[Transaction])
def get_recent_transactions(
    customer_id: str, limit: int = Query(default=10, ge=1, le=50)
) -> list[Transaction]:
    record = get_customer_or_404(customer_id)
    return record.transactions[:limit]
