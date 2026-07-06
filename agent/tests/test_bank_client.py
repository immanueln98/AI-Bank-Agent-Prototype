import httpx
import pytest
import respx

from bankagent_agent.bank_client import BankAPIError, BankClient
from bankagent_agent.config import AgentSettings

BASE = "http://backend.test"


@pytest.fixture
def settings() -> AgentSettings:
    return AgentSettings(backend_base_url=BASE, _env_file=None)  # type: ignore[call-arg]


@pytest.fixture
async def client(settings: AgentSettings) -> BankClient:
    async with BankClient(settings) as c:
        yield c


@respx.mock
async def test_verify_parses_model(client: BankClient) -> None:
    respx.post(f"{BASE}/api/v1/verify").respond(
        200, json={"verified": True, "customer_id": "cust-001", "first_name": "Thabo"}
    )
    result = await client.verify("1002345678", "9087")
    assert result.verified is True
    assert result.customer_id == "cust-001"


@respx.mock
async def test_retries_on_5xx_then_succeeds(client: BankClient) -> None:
    route = respx.get(f"{BASE}/api/v1/customers/cust-001")
    route.side_effect = [
        httpx.Response(500),
        httpx.Response(500),
        httpx.Response(
            200,
            json={
                "customer_id": "cust-001",
                "full_name": "Thabo Mokoena",
                "first_name": "Thabo",
                "accounts": [],
            },
        ),
    ]
    profile = await client.get_customer_profile("cust-001")
    assert profile.full_name == "Thabo Mokoena"
    assert route.call_count == 3


@respx.mock
async def test_gives_up_after_three_5xx(client: BankClient) -> None:
    route = respx.get(f"{BASE}/api/v1/customers/cust-001").respond(500)
    with pytest.raises(BankAPIError) as excinfo:
        await client.get_customer_profile("cust-001")
    assert excinfo.value.status_code == 503
    assert route.call_count == 3


@respx.mock
async def test_retries_on_timeout(client: BankClient) -> None:
    route = respx.get(f"{BASE}/api/v1/customers/cust-001")
    route.side_effect = httpx.ConnectTimeout("boom")
    with pytest.raises(BankAPIError) as excinfo:
        await client.get_customer_profile("cust-001")
    assert excinfo.value.status_code == 503
    assert route.call_count == 3


@respx.mock
async def test_404_is_not_retried(client: BankClient) -> None:
    route = respx.get(f"{BASE}/api/v1/customers/cust-999").respond(
        404, json={"detail": "Unknown customer"}
    )
    with pytest.raises(BankAPIError) as excinfo:
        await client.get_customer_profile("cust-999")
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Unknown customer"
    assert route.call_count == 1


@respx.mock
async def test_409_surfaces_detail(client: BankClient) -> None:
    respx.post(f"{BASE}/api/v1/customers/cust-004/card/report-lost").respond(
        409, json={"detail": "Card is already blocked"}
    )
    with pytest.raises(BankAPIError) as excinfo:
        await client.report_card_lost("cust-004", "7742")
    assert excinfo.value.status_code == 409


@respx.mock
async def test_transactions_limit_param_and_parsing(client: BankClient) -> None:
    route = respx.get(f"{BASE}/api/v1/customers/cust-001/transactions").respond(
        200,
        json=[
            {
                "transaction_id": "txn-1",
                "ts": "2026-07-03",
                "merchant": "Checkers",
                "description": "Groceries",
                "amount": -100.5,
                "currency": "ZAR",
                "status": "posted",
            }
        ],
    )
    txns = await client.get_recent_transactions("cust-001", limit=5)
    assert txns[0].merchant == "Checkers"
    assert route.calls[0].request.url.params["limit"] == "5"


@respx.mock
async def test_escalation_round_trip(client: BankClient) -> None:
    respx.post(f"{BASE}/api/v1/escalations").respond(
        200, json={"ticket_ref": "ESC-20260706-001", "queue": "general-support"}
    )
    ticket = await client.create_escalation("out_of_scope", "summary", customer_id="cust-005")
    assert ticket.ticket_ref == "ESC-20260706-001"
