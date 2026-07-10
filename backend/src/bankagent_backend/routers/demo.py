"""Demo-only endpoints backing the frontend demo console.

Serves the presenter cheat-sheets (which fixture customer to "be", what to
say) and the simulated customer phone (what code the banking app would be
showing). Not part of the bank-API surface - a real deployment deletes this
router entirely; the step-up code would exist only on the customer's device.
"""

from fastapi import APIRouter

from bankagent_shared.models import ScenarioInfo, StepUpChallenge

from ..fixtures import SCENARIOS
from .stepup import latest_challenge

router = APIRouter()


@router.get("/demo/scenarios", response_model=list[ScenarioInfo])
def list_scenarios() -> list[ScenarioInfo]:
    return SCENARIOS


@router.get("/demo/stepup/latest", response_model=StepUpChallenge | None)
def latest_step_up_challenge() -> StepUpChallenge | None:
    """What the customer's phone is showing right now (simulated)."""
    challenge = latest_challenge()
    if challenge is None or not challenge.alive:
        return None
    return StepUpChallenge(
        customer_first_name=challenge.customer_first_name,
        code=challenge.code,
        sent_at=challenge.sent_at,
    )
