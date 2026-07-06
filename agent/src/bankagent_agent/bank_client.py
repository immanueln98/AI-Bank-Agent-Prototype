"""HTTP client for the mock bank backend.

The single transport layer for every agent tool: timeouts, retries, and typed
parsing live here so each new tool inherits them. Only transport failures and
5xx responses are retried; 4xx responses raise :class:`BankAPIError`
immediately (retrying a 404 won't make the customer exist).
"""

from __future__ import annotations

from types import TracebackType
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from bankagent_shared import get_logger
from bankagent_shared.models import (
    CardActionResult,
    CustomerProfile,
    DisputeResult,
    EscalationTicket,
    FaqResult,
    Transaction,
    VerificationResult,
)

from .config import AgentSettings

log = get_logger(__name__)


class BankAPIError(Exception):
    """A definitive backend failure (after retries, or a 4xx)."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(f"{status_code}: {detail}")
        self.status_code = status_code
        self.detail = detail


class _ServerError(Exception):
    """Internal marker for retryable 5xx responses."""


class BankClient:
    def __init__(self, settings: AgentSettings) -> None:
        self._http = httpx.AsyncClient(
            base_url=settings.backend_base_url,
            timeout=httpx.Timeout(settings.backend_timeout_seconds, connect=2.0),
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> BankClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    @retry(
        retry=retry_if_exception_type((httpx.TransportError, _ServerError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.2, max=1.5),
        reraise=True,
    )
    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        response = await self._http.request(method, path, **kwargs)
        if response.status_code >= 500:
            raise _ServerError(f"{response.status_code} from {path}")
        return response

    async def _call(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            response = await self._request(method, path, **kwargs)
        except (httpx.TransportError, _ServerError) as exc:
            log.warning("bank_api_unreachable", path=path, error=str(exc))
            raise BankAPIError(503, "banking system unreachable") from exc
        if response.status_code >= 400:
            try:
                detail = str(response.json().get("detail", response.text))
            except ValueError:
                detail = response.text
            raise BankAPIError(response.status_code, detail)
        return response

    # ------------------------------------------------------------------
    # One method per backend endpoint; adding a tool starts here.
    # ------------------------------------------------------------------
    async def verify(self, account_number: str, id_last4: str) -> VerificationResult:
        response = await self._call(
            "POST",
            "/api/v1/verify",
            json={"account_number": account_number, "id_last4": id_last4},
        )
        return VerificationResult.model_validate(response.json())

    async def get_customer_profile(self, customer_id: str) -> CustomerProfile:
        response = await self._call("GET", f"/api/v1/customers/{customer_id}")
        return CustomerProfile.model_validate(response.json())

    async def get_recent_transactions(self, customer_id: str, limit: int = 10) -> list[Transaction]:
        response = await self._call(
            "GET", f"/api/v1/customers/{customer_id}/transactions", params={"limit": limit}
        )
        return [Transaction.model_validate(t) for t in response.json()]

    async def report_card_lost(self, customer_id: str, card_last4: str) -> CardActionResult:
        response = await self._call(
            "POST",
            f"/api/v1/customers/{customer_id}/card/report-lost",
            json={"card_last4": card_last4},
        )
        return CardActionResult.model_validate(response.json())

    async def dispute_transaction(
        self, customer_id: str, transaction_id: str, reason: str
    ) -> DisputeResult:
        response = await self._call(
            "POST",
            f"/api/v1/customers/{customer_id}/disputes",
            json={"transaction_id": transaction_id, "reason": reason},
        )
        return DisputeResult.model_validate(response.json())

    async def search_faq(self, query: str) -> list[FaqResult]:
        response = await self._call("GET", "/api/v1/faq/search", params={"q": query})
        return [FaqResult.model_validate(f) for f in response.json()]

    async def create_escalation(
        self, reason: str, summary: str, customer_id: str | None = None
    ) -> EscalationTicket:
        response = await self._call(
            "POST",
            "/api/v1/escalations",
            json={"customer_id": customer_id, "reason": reason, "summary": summary},
        )
        return EscalationTicket.model_validate(response.json())
