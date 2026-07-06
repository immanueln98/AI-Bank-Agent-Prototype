"""Demo-only endpoints backing the frontend scenario picker.

Serves the presenter cheat-sheets (which fixture customer to "be", what to
say). Not part of the bank-API surface - a real deployment deletes this router.
"""

from fastapi import APIRouter

from bankagent_shared.models import ScenarioInfo

from ..fixtures import SCENARIOS

router = APIRouter()


@router.get("/demo/scenarios", response_model=list[ScenarioInfo])
def list_scenarios() -> list[ScenarioInfo]:
    return SCENARIOS
