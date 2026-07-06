"""Streams tool-activity events to the demo frontend's activity panel.

Events go out as JSON text streams on ``TOOL_EVENTS_TOPIC``; the browser
subscribes with ``room.registerTextStreamHandler``. Everything is PII-masked
before it leaves the process. Emission failures never break a tool call -
the demo panel going stale is better than the call dropping.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from bankagent_shared import TOOL_EVENTS_TOPIC, KnownPII, ToolEvent, get_logger
from bankagent_shared.redaction import mask_mapping, mask_text

if TYPE_CHECKING:
    from livekit import rtc

log = get_logger(__name__)


class ToolEventEmitter:
    def __init__(self, known_pii: KnownPII) -> None:
        self._known = known_pii
        self._room: rtc.Room | None = None
        self._listeners: list[Callable[[ToolEvent], None]] = []

    def attach_room(self, room: rtc.Room) -> None:
        self._room = room

    def add_listener(self, listener: Callable[[ToolEvent], None]) -> None:
        """Local subscribers (e.g. the transcript recorder)."""
        self._listeners.append(listener)

    async def emit(self, event: ToolEvent) -> None:
        masked = event.model_copy(
            update={
                "args_masked": mask_mapping(event.args_masked, self._known),
                "result_summary": (
                    mask_text(event.result_summary, self._known) if event.result_summary else None
                ),
                "error": mask_text(event.error, self._known) if event.error else None,
            }
        )
        log.info("tool_event", **masked.model_dump(exclude_none=True))
        for listener in self._listeners:
            listener(masked)
        if self._room is not None:
            try:
                await self._room.local_participant.send_text(
                    masked.model_dump_json(), topic=TOOL_EVENTS_TOPIC
                )
            except Exception as exc:
                log.warning("tool_event_publish_failed", error=str(exc))
