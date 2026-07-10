from fastapi.testclient import TestClient


def _send(client: TestClient, customer_id: str = "cust-001") -> str:
    resp = client.post(f"/api/v1/customers/{customer_id}/stepup/send")
    assert resp.status_code == 200
    assert "Meridian app" in resp.json()["sent_to"]
    # The code itself is only visible via the demo phone-sim endpoint.
    return client.get("/api/v1/demo/stepup/latest").json()["code"]


class TestSendAndDemoView:
    def test_send_issues_six_digit_code_visible_on_demo_phone(self, client: TestClient) -> None:
        code = _send(client)
        assert len(code) == 6 and code.isdigit()
        challenge = client.get("/api/v1/demo/stepup/latest").json()
        assert challenge["customer_first_name"] == "Thabo"

    def test_no_challenge_yet_returns_null(self, client: TestClient) -> None:
        assert client.get("/api/v1/demo/stepup/latest").json() is None

    def test_resend_replaces_the_visible_code(self, client: TestClient) -> None:
        _send(client)
        second = _send(client)
        # The newest code is what the customer's phone shows and what verifies.
        assert client.get("/api/v1/demo/stepup/latest").json()["code"] == second

    def test_unknown_customer_404(self, client: TestClient) -> None:
        assert client.post("/api/v1/customers/nope/stepup/send").status_code == 404


class TestVerify:
    def test_correct_code_verifies_and_is_single_use(self, client: TestClient) -> None:
        code = _send(client)
        resp = client.post(
            "/api/v1/customers/cust-001/stepup/verify", json={"code": f" {code[:3]} {code[3:]} "}
        ).json()
        assert resp["verified"] is True
        # Consumed: the same code cannot be replayed...
        replay = client.post("/api/v1/customers/cust-001/stepup/verify", json={"code": code}).json()
        assert replay["verified"] is False
        # ...and the demo phone no longer shows it.
        assert client.get("/api/v1/demo/stepup/latest").json() is None

    def test_three_wrong_attempts_kill_the_code(self, client: TestClient) -> None:
        code = _send(client)
        wrong = "000000" if code != "000000" else "111111"
        for expected_remaining in (2, 1, 0):
            resp = client.post(
                "/api/v1/customers/cust-001/stepup/verify", json={"code": wrong}
            ).json()
            assert resp["verified"] is False
            assert resp["attempts_remaining"] == expected_remaining
        # Even the CORRECT code is dead now - a fresh send is required.
        resp = client.post("/api/v1/customers/cust-001/stepup/verify", json={"code": code}).json()
        assert resp["verified"] is False
        assert resp["attempts_remaining"] == 0

    def test_verify_without_any_send_fails_safely(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/customers/cust-001/stepup/verify", json={"code": "123456"}
        ).json()
        assert resp == {"verified": False, "attempts_remaining": 0}

    def test_codes_are_scoped_per_customer(self, client: TestClient) -> None:
        code = _send(client, "cust-001")
        resp = client.post("/api/v1/customers/cust-002/stepup/verify", json={"code": code}).json()
        assert resp["verified"] is False
