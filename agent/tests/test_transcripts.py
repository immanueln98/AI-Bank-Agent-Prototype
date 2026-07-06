import json
from dataclasses import dataclass
from pathlib import Path

from livekit.agents.llm import ChatMessage

from bankagent_agent.transcripts import TranscriptRecorder
from bankagent_shared import KnownPII, ToolEvent


@dataclass
class _FakeItemEvent:
    item: ChatMessage


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_messages_are_masked_on_disk(tmp_path: Path) -> None:
    known = KnownPII()
    known.add("1002345678")
    recorder = TranscriptRecorder(tmp_path, "sess123", known)

    recorder._on_item(
        _FakeItemEvent(item=ChatMessage(role="user", content=["my account is 10 0234 5678"]))
    )
    recorder._on_item(
        _FakeItemEvent(item=ChatMessage(role="assistant", content=["ID 9001015009087 noted"]))
    )

    records = _read_jsonl(recorder.path)
    assert records[0]["role"] == "user"
    assert "5678" in records[0]["content"]
    assert "1002345678" not in records[0]["content"]
    assert "10 0234 5678" not in records[0]["content"]
    assert "9001015009087" not in records[1]["content"]  # regex safety net


def test_tool_events_and_finalize_appended(tmp_path: Path) -> None:
    recorder = TranscriptRecorder(tmp_path, "sess456", KnownPII())
    recorder.record_tool_event(
        ToolEvent(type="tool_call_finished", tool="get_customer_profile", result_summary="ok")
    )
    recorder.finalize({"verified_customer": "Thabo", "escalated": False})

    records = _read_jsonl(recorder.path)
    kinds = [r["kind"] for r in records]
    assert kinds == ["tool_event", "session_end"]
    assert records[0]["tool"] == "get_customer_profile"
    assert records[1]["duration_seconds"] >= 0


def test_files_grouped_by_day(tmp_path: Path) -> None:
    recorder = TranscriptRecorder(tmp_path, "sess789", KnownPII())
    recorder.finalize({})
    day_dirs = [p for p in tmp_path.iterdir() if p.is_dir()]
    assert len(day_dirs) == 1
    assert (day_dirs[0] / "sess789.jsonl").exists()
