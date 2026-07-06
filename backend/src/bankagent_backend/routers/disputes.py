"""Transaction disputes. PRODUCTION NOTE: replace with the bank's disputes/fraud API."""

from uuid import uuid4

from fastapi import APIRouter, HTTPException

from bankagent_shared import get_logger
from bankagent_shared.models import DisputeRequest, DisputeResult

from .customers import get_customer_or_404

router = APIRouter()
log = get_logger(__name__)

DISPUTE_SLA_DAYS = 10


@router.post("/customers/{customer_id}/disputes", response_model=DisputeResult)
def dispute_transaction(customer_id: str, req: DisputeRequest) -> DisputeResult:
    record = get_customer_or_404(customer_id)
    if not any(t.transaction_id == req.transaction_id for t in record.transactions):
        raise HTTPException(status_code=404, detail="Unknown transaction for this customer")
    if req.transaction_id in record.disputed_transaction_ids:
        raise HTTPException(status_code=409, detail="A dispute already exists for this transaction")

    record.disputed_transaction_ids.add(req.transaction_id)
    dispute_id = f"DSP-{uuid4().hex[:8].upper()}"
    log.info(
        "dispute_created",
        customer_id=customer_id,
        transaction_id=req.transaction_id,
        dispute_id=dispute_id,
    )
    return DisputeResult(
        dispute_id=dispute_id,
        transaction_id=req.transaction_id,
        status="under_review",
        sla_days=DISPUTE_SLA_DAYS,
    )
