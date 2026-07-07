"""Read-only access to the agent's on-disk call transcripts.

The agent writes one PII-masked JSONL file per call to
``transcripts/<YYYY-MM-DD>/<session_id>.jsonl`` (both services share the
directory: same working directory under `make dev`, a shared volume under
docker compose). Everything in the files was masked before it touched disk,
so serving them to the supervisor view is safe.

PRODUCTION NOTE: transcripts move to object storage with retention schedules
and access control; this router becomes a thin proxy over that store.

Session ids are matched against files found by globbing - user input is never
joined into a filesystem path.
"""

import json
import re
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException

from bankagent_shared import get_logger
from bankagent_shared.models import TranscriptDetail, TranscriptMeta

from ..config import BackendSettings

router = APIRouter()
log = get_logger(__name__)

_SESSION_ID = re.compile(r"[0-9a-f]{6,32}")


def _transcript_files(transcripts_dir: Path) -> list[Path]:
    if not transcripts_dir.is_dir():
        return []
    files = [
        f
        for f in transcripts_dir.glob("*/*.jsonl")
        if _SESSION_ID.fullmatch(f.stem) and f.is_file()
    ]
    return sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)


def _parse_entries(path: Path) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    try:
        raw_lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        log.warning("transcript_read_failed", path=str(path), error=str(exc))
        raise HTTPException(status_code=404, detail="Transcript unavailable") from exc
    for line in raw_lines:
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except ValueError:
            continue  # a torn line from a crashed session; keep the rest
        if isinstance(entry, dict):
            entries.append(entry)
    return entries


def _meta_for(path: Path) -> TranscriptMeta:
    entries = _parse_entries(path)
    end = next((e for e in entries if e.get("kind") == "session_end"), None)
    duration = end.get("duration_seconds") if end else None
    customer = end.get("verified_customer") if end else None
    return TranscriptMeta(
        session_id=path.stem,
        date=path.parent.name,
        modified_at=datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).isoformat(
            timespec="seconds"
        ),
        messages=sum(1 for e in entries if e.get("kind") == "message"),
        tool_events=sum(1 for e in entries if e.get("kind") == "tool_event"),
        duration_seconds=float(duration) if isinstance(duration, int | float) else None,
        customer=str(customer) if customer else None,
        escalated=bool(end.get("escalated")) if end else False,
        ended=end is not None,
    )


@router.get("/transcripts", response_model=list[TranscriptMeta])
def list_transcripts(limit: int = 50) -> list[TranscriptMeta]:
    settings = BackendSettings()
    files = _transcript_files(settings.transcripts_dir)[: max(1, min(limit, 200))]
    return [_meta_for(f) for f in files]


@router.get("/transcripts/{session_id}", response_model=TranscriptDetail)
def get_transcript(session_id: str) -> TranscriptDetail:
    settings = BackendSettings()
    for path in _transcript_files(settings.transcripts_dir):
        if path.stem == session_id:
            return TranscriptDetail(
                session_id=session_id, date=path.parent.name, entries=_parse_entries(path)
            )
    raise HTTPException(status_code=404, detail="No transcript with that session id")
