import jwt
from fastapi.testclient import TestClient

SECRET = "test-secret-value-of-at-least-32-chars!!"


class TestLiveKitToken:
    def test_mints_decodable_token_with_room_grant(self, client: TestClient) -> None:
        resp = client.post("/api/v1/livekit/token", json={"scenario": "naledi"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["url"] == "wss://test.livekit.cloud"
        assert body["room"].startswith("demo-naledi-")

        claims = jwt.decode(
            body["token"], SECRET, algorithms=["HS256"], options={"verify_aud": False}
        )
        assert claims["iss"] == "test-api-key"
        assert claims["video"]["roomJoin"] is True
        assert claims["video"]["room"] == body["room"]
        assert claims["sub"].startswith("caller-")

    def test_token_dispatches_the_named_agent(self, client: TestClient) -> None:
        """The worker uses explicit dispatch (shared with the SIP path), so a
        browser token without an agent request would ring into an empty room."""
        body = client.post("/api/v1/livekit/token", json={"scenario": "thabo"}).json()
        claims = jwt.decode(
            body["token"], SECRET, algorithms=["HS256"], options={"verify_aud": False}
        )
        agents = claims["roomConfig"]["agents"]
        assert [a["agentName"] for a in agents] == ["meridian-bank-agent"]

    def test_rooms_are_unique_per_call(self, client: TestClient) -> None:
        room1 = client.post("/api/v1/livekit/token", json={"scenario": "thabo"}).json()["room"]
        room2 = client.post("/api/v1/livekit/token", json={"scenario": "thabo"}).json()["room"]
        assert room1 != room2

    def test_no_scenario_defaults_to_adhoc_room(self, client: TestClient) -> None:
        body = client.post("/api/v1/livekit/token", json={}).json()
        assert body["room"].startswith("demo-adhoc-")
