from fastapi.testclient import TestClient


class TestFaqSearch:
    def test_finds_relevant_answer(self, client: TestClient) -> None:
        resp = client.get("/api/v1/faq/search", params={"q": "branch hours"})
        assert resp.status_code == 200
        results = resp.json()
        assert results
        assert "operating hours" in results[0]["question"].lower()

    def test_results_ranked_by_score(self, client: TestClient) -> None:
        results = client.get(
            "/api/v1/faq/search", params={"q": "how long does a replacement card take"}
        ).json()
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)
        assert "card" in results[0]["question"].lower()

    def test_no_match_returns_empty(self, client: TestClient) -> None:
        assert client.get("/api/v1/faq/search", params={"q": "zebra spaceship"}).json() == []

    def test_short_query_validation(self, client: TestClient) -> None:
        assert client.get("/api/v1/faq/search", params={"q": "x"}).status_code == 422


class TestDemoScenarios:
    def test_lists_five_scenarios(self, client: TestClient) -> None:
        resp = client.get("/api/v1/demo/scenarios")
        assert resp.status_code == 200
        scenarios = resp.json()
        assert len(scenarios) == 5
        ids = {s["id"] for s in scenarios}
        assert ids == {"thabo", "naledi", "kagiso", "amogelang", "sipho"}

    def test_cheatsheets_have_credentials_and_lines(self, client: TestClient) -> None:
        for s in client.get("/api/v1/demo/scenarios").json():
            assert len(s["account_number"]) == 10
            assert len(s["id_last4"]) == 4
            assert s["suggested_lines"]


class TestHealthAndDocs:
    def test_health(self, client: TestClient) -> None:
        assert client.get("/health").json() == {"status": "ok"}

    def test_openapi_docs_enabled(self, client: TestClient) -> None:
        assert client.get("/openapi.json").status_code == 200
        assert client.get("/docs").status_code == 200
