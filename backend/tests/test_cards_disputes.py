from fastapi.testclient import TestClient


class TestReportCardLost:
    def test_blocks_active_card(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/customers/cust-004/card/report-lost", json={"card_last4": "7742"}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "blocked"
        assert body["replacement_eta_days"] == 5
        assert body["reference"].startswith("CARD-")
        # Profile reflects the block afterwards.
        profile = client.get("/api/v1/customers/cust-004").json()
        assert profile["card"]["status"] == "blocked"

    def test_second_report_conflicts(self, client: TestClient) -> None:
        first = client.post(
            "/api/v1/customers/cust-004/card/report-lost", json={"card_last4": "7742"}
        )
        assert first.status_code == 200
        second = client.post(
            "/api/v1/customers/cust-004/card/report-lost", json={"card_last4": "7742"}
        )
        assert second.status_code == 409

    def test_wrong_last4_404(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/customers/cust-004/card/report-lost", json={"card_last4": "0000"}
        )
        assert resp.status_code == 404

    def test_unknown_customer_404(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/customers/cust-999/card/report-lost", json={"card_last4": "7742"}
        )
        assert resp.status_code == 404


class TestDisputes:
    FLAGGED_TXN = "txn-002-010"

    def test_creates_dispute_for_flagged_transaction(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/customers/cust-002/disputes",
            json={"transaction_id": self.FLAGGED_TXN, "reason": "Caller does not recognise it"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["dispute_id"].startswith("DSP-")
        assert body["status"] == "under_review"
        assert body["sla_days"] == 10

    def test_duplicate_dispute_conflicts(self, client: TestClient) -> None:
        payload = {"transaction_id": self.FLAGGED_TXN, "reason": "dup"}
        assert client.post("/api/v1/customers/cust-002/disputes", json=payload).status_code == 200
        assert client.post("/api/v1/customers/cust-002/disputes", json=payload).status_code == 409

    def test_unknown_transaction_404(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/customers/cust-002/disputes",
            json={"transaction_id": "txn-does-not-exist", "reason": "x"},
        )
        assert resp.status_code == 404


class TestEscalations:
    def test_creates_ticket_with_reference(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/escalations",
            json={
                "customer_id": "cust-005",
                "reason": "customer_requested_human",
                "summary": "Verified customer asked about investing; needs a consultant.",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["ticket_ref"].startswith("ESC-")
        assert body["queue"] == "general-support"

    def test_ticket_refs_increment(self, client: TestClient) -> None:
        payload = {"reason": "r", "summary": "s"}
        ref1 = client.post("/api/v1/escalations", json=payload).json()["ticket_ref"]
        ref2 = client.post("/api/v1/escalations", json=payload).json()["ticket_ref"]
        assert ref1 != ref2
        assert ref1.endswith("-001") and ref2.endswith("-002")

    def test_customer_id_optional(self, client: TestClient) -> None:
        resp = client.post("/api/v1/escalations", json={"reason": "r", "summary": "s"})
        assert resp.status_code == 200
