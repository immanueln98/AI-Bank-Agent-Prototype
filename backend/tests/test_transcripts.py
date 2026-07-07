import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def _write_transcript(root: Path, date: str, session_id: str, entries: list[dict]) -> Path:
    day_dir = root / date
    day_dir.mkdir(parents=True, exist_ok=True)
    path = day_dir / f"{session_id}.jsonl"
    path.write_text("\n".join(json.dumps(e) for e in entries) + "\n", encoding="utf-8")
    return path


ENTRIES = [
    {"ts": "2026-07-07T10:00:01+00:00", "kind": "message", "role": "assistant", "content": "Hi"},
    {"ts": "2026-07-07T10:00:09+00:00", "kind": "message", "role": "user", "content": "Balance?"},
    {
        "kind": "tool_event",
        "type": "tool_call_finished",
        "tool": "get_customer_profile",
        "result_summary": "Thabo Mokoena: 2 account(s)",
        "duration_ms": 412,
    },
    {
        "ts": "2026-07-07T10:02:41+00:00",
        "kind": "session_end",
        "duration_seconds": 161.0,
        "verified_customer": "Thabo",
        "escalated": False,
    },
]


@pytest.fixture
def transcripts_client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, client: TestClient
) -> tuple[TestClient, Path]:
    monkeypatch.setenv("TRANSCRIPTS_DIR", str(tmp_path))
    return client, tmp_path


class TestListTranscripts:
    def test_empty_dir_and_missing_dir_return_empty(self, transcripts_client) -> None:
        client, _ = transcripts_client
        assert client.get("/api/v1/transcripts").json() == []

    def test_lists_with_summary_newest_first(self, transcripts_client) -> None:
        client, root = transcripts_client
        old = _write_transcript(root, "2026-07-06", "aaaa11112222", ENTRIES[:2])
        import os

        os.utime(old, (1e9, 1e9))  # force old mtime
        _write_transcript(root, "2026-07-07", "bbbb33334444", ENTRIES)

        listed = client.get("/api/v1/transcripts").json()
        assert [t["session_id"] for t in listed] == ["bbbb33334444", "aaaa11112222"]
        full = listed[0]
        assert full["messages"] == 2
        assert full["tool_events"] == 1
        assert full["duration_seconds"] == 161.0
        assert full["customer"] == "Thabo"
        assert full["ended"] is True
        crashed = listed[1]
        assert crashed["ended"] is False
        assert crashed["duration_seconds"] is None

    def test_ignores_non_session_files(self, transcripts_client) -> None:
        client, root = transcripts_client
        (root / "2026-07-07").mkdir(parents=True)
        (root / "2026-07-07" / "NOT-A-SESSION.jsonl").write_text("{}", encoding="utf-8")
        assert client.get("/api/v1/transcripts").json() == []


class TestGetTranscript:
    def test_full_entries_round_trip(self, transcripts_client) -> None:
        client, root = transcripts_client
        _write_transcript(root, "2026-07-07", "bbbb33334444", ENTRIES)
        detail = client.get("/api/v1/transcripts/bbbb33334444").json()
        assert detail["date"] == "2026-07-07"
        assert len(detail["entries"]) == 4
        assert detail["entries"][0]["role"] == "assistant"

    def test_torn_lines_are_skipped(self, transcripts_client) -> None:
        client, root = transcripts_client
        path = _write_transcript(root, "2026-07-07", "bbbb33334444", ENTRIES[:1])
        with path.open("a", encoding="utf-8") as fh:
            fh.write('{"kind": "mess')  # crashed mid-write
        entries = client.get("/api/v1/transcripts/bbbb33334444").json()["entries"]
        assert len(entries) == 1

    def test_unknown_and_traversal_ids_404(self, transcripts_client) -> None:
        client, root = transcripts_client
        _write_transcript(root, "2026-07-07", "bbbb33334444", ENTRIES)
        assert client.get("/api/v1/transcripts/ffffffffffff").status_code == 404
        assert client.get("/api/v1/transcripts/..%2F..%2Fetc").status_code == 404
