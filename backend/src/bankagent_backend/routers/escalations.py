"""Simulated human-handoff queue.

PRODUCTION NOTE: this is where a real contact-centre integration goes (Genesys,
Amazon Connect, in-house CRM ticketing). The agent already sends a structured
reason + conversation summary, so a human picks up with full context.
"""

from datetime import UTC, datetime

from fastapi import APIRouter

from bankagent_shared import get_logger
from bankagent_shared.models import EscalationRequest, EscalationTicket

from ..fixtures import next_escalation_ref

router = APIRouter()
log = get_logger(__name__)


@router.post("/escalations", response_model=EscalationTicket)
def create_escalation(req: EscalationRequest) -> EscalationTicket:
    ticket_ref = next_escalation_ref(datetime.now(UTC).strftime("%Y%m%d"))
    log.info(
        "escalation_created",
        ticket_ref=ticket_ref,
        customer_id=req.customer_id,
        reason=req.reason,
        summary=req.summary,
    )
    return EscalationTicket(ticket_ref=ticket_ref, queue="general-support")
