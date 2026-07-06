from fastapi.testclient import TestClient

THABO_ACCOUNT = "1002345678"
THABO_ID_LAST4 = "9087"


class TestVerify:
    def test_correct_details_verify(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/verify",
            json={"account_number": THABO_ACCOUNT, "id_last4": THABO_ID_LAST4},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["verified"] is True
        assert body["customer_id"] == "cust-001"
        assert body["first_name"] == "Thabo"

    def test_wrong_id_returns_unverified_not_error(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/verify",
            json={"account_number": THABO_ACCOUNT, "id_last4": "0000"},
        )
        assert resp.status_code == 200
        assert resp.json() == {"verified": False, "customer_id": None, "first_name": None}

    def test_unknown_account_404(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/verify", json={"account_number": "9999999999", "id_last4": "1234"}
        )
        assert resp.status_code == 404

    def test_spoken_account_number_with_spaces_accepted(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/verify",
            json={"account_number": "10 0234 5678", "id_last4": THABO_ID_LAST4},
        )
        assert resp.status_code == 200
        assert resp.json()["verified"] is True


class TestProfile:
    def test_profile_includes_accounts_and_card(self, client: TestClient) -> None:
        resp = client.get("/api/v1/customers/cust-001")
        assert resp.status_code == 200
        body = resp.json()
        assert body["full_name"] == "Thabo Mokoena"
        assert len(body["accounts"]) == 2
        assert body["card"]["status"] == "active"
        # Full account numbers must never appear in profile responses.
        assert THABO_ACCOUNT not in resp.text

    def test_unknown_customer_404(self, client: TestClient) -> None:
        assert client.get("/api/v1/customers/cust-999").status_code == 404

    def test_kagiso_is_near_credit_limit(self, client: TestClient) -> None:
        body = client.get("/api/v1/customers/cust-003").json()
        credit = next(a for a in body["accounts"] if a["type"] == "credit")
        assert credit["available_credit"] == 1250.00
        assert credit["credit_limit"] == 20000.00


class TestTransactions:
    def test_returns_limited_transactions(self, client: TestClient) -> None:
        resp = client.get("/api/v1/customers/cust-001/transactions", params={"limit": 3})
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_naledi_has_flagged_transaction(self, client: TestClient) -> None:
        resp = client.get("/api/v1/customers/cust-002/transactions")
        flagged = [t for t in resp.json() if t["status"] == "flagged"]
        assert len(flagged) == 1
        assert "Luxembourg" in flagged[0]["description"]

    def test_thabo_salary_is_most_recent_credit(self, client: TestClient) -> None:
        txns = client.get("/api/v1/customers/cust-001/transactions").json()
        salary = [t for t in txns if "SALARY" in t["description"]]
        assert salary and salary[0]["amount"] > 0

    def test_unknown_customer_404(self, client: TestClient) -> None:
        assert client.get("/api/v1/customers/cust-999/transactions").status_code == 404

    def test_limit_validation(self, client: TestClient) -> None:
        resp = client.get("/api/v1/customers/cust-001/transactions", params={"limit": 0})
        assert resp.status_code == 422
