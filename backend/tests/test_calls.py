from typing import Any

from fastapi.testclient import TestClient


def _record(session_id: str, **overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "session_id": session_id,
        "room": f"demo-thabo-{session_id}",
        "scenario": "thabo",
        "started_at": "2026-07-07T09:00:00+00:00",
        "ended_at": "2026-07-07T09:03:20+00:00",
        "duration_seconds": 200.0,
        "outcome": "contained",
        "verified": True,
        "customer_first_name": "Thabo",
        "account_masked": "****5678",
        "tools_used": ["verify_identity", "get_customer_profile"],
        "tool_calls": 2,
        "events": [
            {
                "type": "tool_call_finished",
                "tool": "verify_identity",
                "result_summary": "Identity verified: Thabo (****5678)",
            }
        ],
    }
    base.update(overrides)
    return base


class TestStoreAndFetch:
    def test_post_stores_and_returns_record(self, client: TestClient) -> None:
        resp = client.post("/api/v1/calls", json=_record("s1"))
        assert resp.status_code == 201
        assert resp.json()["session_id"] == "s1"
        assert client.get("/api/v1/calls/s1").json()["outcome"] == "contained"

    def test_list_newest_first(self, client: TestClient) -> None:
        client.post("/api/v1/calls", json=_record("s1"))
        client.post("/api/v1/calls", json=_record("s2"))
        listed = client.get("/api/v1/calls").json()
        assert [r["session_id"] for r in listed] == ["s2", "s1"]

    def test_repost_same_session_replaces(self, client: TestClient) -> None:
        client.post("/api/v1/calls", json=_record("s1"))
        client.post("/api/v1/calls", json=_record("s1", outcome="escalated", escalated=True))
        listed = client.get("/api/v1/calls").json()
        assert len(listed) == 1
        assert listed[0]["outcome"] == "escalated"

    def test_unknown_session_404(self, client: TestClient) -> None:
        assert client.get("/api/v1/calls/nope").status_code == 404

    def test_audit_events_round_trip(self, client: TestClient) -> None:
        client.post("/api/v1/calls", json=_record("s1"))
        events = client.get("/api/v1/calls/s1").json()["events"]
        assert events[0]["tool"] == "verify_identity"
        assert "****5678" in events[0]["result_summary"]


class TestMetrics:
    def test_empty_store_returns_zeroes(self, client: TestClient) -> None:
        metrics = client.get("/api/v1/calls/metrics").json()
        assert metrics["total_calls"] == 0
        assert metrics["containment_rate"] is None

    def test_aggregates_outcomes(self, client: TestClient) -> None:
        client.post("/api/v1/calls", json=_record("s1"))
        client.post("/api/v1/calls", json=_record("s2", duration_seconds=100.0, tool_calls=4))
        client.post(
            "/api/v1/calls",
            json=_record("s3", outcome="escalated", escalated=True, escalation_ref="ESC-1"),
        )
        client.post(
            "/api/v1/calls",
            json=_record(
                "s4",
                outcome="verification_failed",
                verified=False,
                locked_out=True,
                failed_verification_attempts=3,
            ),
        )
        metrics = client.get("/api/v1/calls/metrics").json()
        assert metrics["total_calls"] == 4
        assert metrics["contained"] == 2
        assert metrics["escalated"] == 1
        assert metrics["verification_failed"] == 1
        assert metrics["lockouts"] == 1
        assert metrics["containment_rate"] == 0.5
        assert metrics["avg_duration_seconds"] == 175.0
