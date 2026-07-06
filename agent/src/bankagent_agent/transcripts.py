"""Per-session transcript persistence for QA and demo replay.

One JSONL file per call at ``transcripts/<YYYY-MM-DD>/<session_id>.jsonl``:
conversation turns, tool events, and a closing summary line. Every string is
PII-masked before it touches disk. Lines are appended as events happen, so a
crashed session still leaves a usable transcript.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from livekit.agents.llm import ChatMessage

from bankagent_shared import KnownPII, ToolEvent, get_logger
from bankagent_shared.redaction import mask_text

if TYPE_CHECKING:
    from livekit.agents import AgentSession
    from livekit.agents.voice.events import ConversationItemAddedEvent

log = get_logger(__name__)


class TranscriptRecorder:
    def __init__(self, transcripts_dir: Path, session_id: str, known_pii: KnownPII) -> None:
        self._known = known_pii
        self._started_at = datetime.now(UTC)
        day_dir = transcripts_dir / self._started_at.strftime("%Y-%m-%d")
        day_dir.mkdir(parents=True, exist_ok=True)
        self._path = day_dir / f"{session_id}.jsonl"

    @property
    def path(self) -> Path:
        return self._path

    def start(self, session: AgentSession[Any]) -> None:
        session.on("conversation_item_added", self._on_item)

    def _on_item(self, event: ConversationItemAddedEvent) -> None:
        item = event.item
        if not isinstance(item, ChatMessage):
            return  # agent handoffs etc. are captured via tool events instead
        content = item.text_content
        if content is None:
            return
        self._append(
            {
                "ts": datetime.now(UTC).isoformat(timespec="milliseconds"),
                "kind": "message",
                "role": item.role,
                "content": mask_text(content, self._known),
                "interrupted": bool(getattr(item, "interrupted", False)),
            }
        )

    def record_tool_event(self, event: ToolEvent) -> None:
        """Wired as a ToolEventEmitter listener; events arrive pre-masked."""
        self._append({"kind": "tool_event", **event.model_dump(exclude_none=True)})

    def finalize(self, summary: dict[str, Any]) -> None:
        duration = (datetime.now(UTC) - self._started_at).total_seconds()
        self._append(
            {
                "ts": datetime.now(UTC).isoformat(timespec="milliseconds"),
                "kind": "session_end",
                "duration_seconds": round(duration, 1),
                **{
                    k: mask_text(str(v), self._known) if isinstance(v, str) else v
                    for k, v in summary.items()
                },
            }
        )
        log.info("transcript_saved", path=str(self._path))

    def _append(self, record: dict[str, Any]) -> None:
        try:
            with self._path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        except OSError as exc:
            log.warning("transcript_write_failed", error=str(exc))
