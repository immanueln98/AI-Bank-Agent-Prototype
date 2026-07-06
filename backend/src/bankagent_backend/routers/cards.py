"""Card actions. PRODUCTION NOTE: replace with the bank's card-management API."""

from uuid import uuid4

from fastapi import APIRouter, HTTPException

from bankagent_shared import get_logger
from bankagent_shared.models import CardActionResult, CardLostRequest

from .customers import get_customer_or_404

router = APIRouter()
log = get_logger(__name__)

REPLACEMENT_ETA_DAYS = 5


@router.post("/customers/{customer_id}/card/report-lost", response_model=CardActionResult)
def report_card_lost(customer_id: str, req: CardLostRequest) -> CardActionResult:
    record = get_customer_or_404(customer_id)
    card = record.profile.card
    if card is None or card.last4 != req.card_last4.strip():
        raise HTTPException(status_code=404, detail="No matching card on this profile")
    if card.status == "blocked":
        raise HTTPException(status_code=409, detail="Card is already blocked")

    card.status = "blocked"  # in-memory fixture mutation; resets on restart
    reference = f"CARD-{uuid4().hex[:8].upper()}"
    log.info("card_blocked", customer_id=customer_id, card_last4=card.last4, reference=reference)
    return CardActionResult(
        card_last4=card.last4,
        status="blocked",
        replacement_eta_days=REPLACEMENT_ETA_DAYS,
        reference=reference,
    )
