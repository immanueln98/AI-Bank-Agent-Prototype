"""Call records + KPI metrics for the supervisor dashboard.

The agent posts one PII-masked :class:`CallRecord` when a session ends; the
frontend's Supervisor view polls the list and the aggregate metrics. Storage
is in-memory (resets on restart, like all POC state).

PRODUCTION NOTE: this is where the contact-centre analytics/QA store goes -
a database with retention schedules, and a feed into the bank's existing
call-centre reporting (calls handled, containment, AHT are the same KPIs
used for human agents).
"""

from fastapi import APIRouter, HTTPException

from bankagent_shared import get_logger
from bankagent_shared.models import CallMetrics, CallRecord

router = APIRouter()
log = get_logger(__name__)

# Newest last; GET endpoints return newest first. Keyed list, not dict, so
# re-posting the same session_id (agent retry) replaces rather than duplicates.
_records: list[CallRecord] = []


def reset_calls() -> None:
    """Restore the empty store. Used by tests."""
    _records.clear()


@router.post("/calls", response_model=CallRecord, status_code=201)
def store_call_record(record: CallRecord) -> CallRecord:
    _records[:] = [r for r in _records if r.session_id != record.session_id]
    _records.append(record)
    log.info(
        "call_record_stored",
        session_id=record.session_id,
        outcome=record.outcome,
        duration_seconds=record.duration_seconds,
        tools=record.tools_used,
    )
    return record


@router.get("/calls/metrics", response_model=CallMetrics)
def call_metrics() -> CallMetrics:
    total = len(_records)
    if total == 0:
        return CallMetrics()
    by_outcome = {"contained": 0, "escalated": 0, "verification_failed": 0, "abandoned": 0}
    for record in _records:
        by_outcome[record.outcome] += 1
    return CallMetrics(
        total_calls=total,
        contained=by_outcome["contained"],
        escalated=by_outcome["escalated"],
        verification_failed=by_outcome["verification_failed"],
        abandoned=by_outcome["abandoned"],
        lockouts=sum(1 for r in _records if r.locked_out),
        containment_rate=round(by_outcome["contained"] / total, 3),
        avg_duration_seconds=round(sum(r.duration_seconds for r in _records) / total, 1),
        avg_tool_calls=round(sum(r.tool_calls for r in _records) / total, 1),
    )


@router.get("/calls", response_model=list[CallRecord])
def list_call_records(limit: int = 50) -> list[CallRecord]:
    return list(reversed(_records[-max(1, min(limit, 200)) :]))


@router.get("/calls/{session_id}", response_model=CallRecord)
def get_call_record(session_id: str) -> CallRecord:
    for record in _records:
        if record.session_id == session_id:
            return record
    raise HTTPException(status_code=404, detail="No call record with that session id")
