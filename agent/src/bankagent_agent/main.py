"""Voice-agent worker entrypoint.

Run modes (LiveKit CLI):
    python -m bankagent_agent.main dev      # local dev worker against LiveKit Cloud
    python -m bankagent_agent.main console  # text/voice chat in the terminal
    python -m bankagent_agent.main start    # production mode (containers)
"""

from __future__ import annotations

import structlog
from dotenv import load_dotenv
from livekit.agents import (
    AgentServer,
    AgentSession,
    JobContext,
    MetricsCollectedEvent,
    cli,
    inference,
    metrics,
)

from bankagent_shared import KnownPII, ToolEvent, configure_logging, get_logger

from .agents.identity_agent import IdentityAgent
from .bank_client import BankAPIError, BankClient
from .call_record import build_call_record
from .config import AgentSettings, build_llm, build_stt, build_tts
from .events import ToolEventEmitter
from .session_state import SessionData
from .transcripts import TranscriptRecorder

log = get_logger(__name__)

# The worker's own LiveKit connection (LIVEKIT_URL/API key) is resolved from
# the process environment by the framework, so .env must actually be exported
# here - unlike AgentSettings, which reads the file itself.
load_dotenv()

server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext) -> None:
    settings = AgentSettings()
    configure_logging(service="bank-agent", fmt=settings.log_format)

    known_pii = KnownPII()
    emitter = ToolEventEmitter(known_pii)
    emitter.attach_room(ctx.room)
    bank = BankClient(settings)
    userdata = SessionData(bank=bank, emitter=emitter, known_pii=known_pii, room_name=ctx.room.name)
    structlog.contextvars.bind_contextvars(session_id=userdata.session_id, room=ctx.room.name)

    recorder = TranscriptRecorder(settings.transcripts_dir, userdata.session_id, known_pii)
    emitter.add_listener(recorder.record_tool_event)

    # Masked audit log for the end-of-call record (supervisor dashboard).
    event_log: list[ToolEvent] = []
    emitter.add_listener(event_log.append)

    session: AgentSession[SessionData] = AgentSession(
        userdata=userdata,
        stt=build_stt(settings),
        llm=build_llm(settings),
        tts=build_tts(settings),
        # VAD defaults to the bundled silero model (weights via `make setup`
        # download-files). Turn detection is LiveKit's hosted audio model
        # (auto-selects v1 on LiveKit Cloud, local v1-mini elsewhere); its
        # presence tightens endpointing to 0.3s min / 2.5s max automatically.
        turn_detection=inference.TurnDetector(),
        preemptive_generation=True,
    )
    recorder.start(session)

    usage = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics(ev: MetricsCollectedEvent) -> None:
        usage.collect(ev.metrics)

    async def _shutdown() -> None:
        recorder.finalize(
            {
                "room": ctx.room.name,
                "verified_customer": userdata.customer_first_name,
                "account": userdata.account_masked,
                "escalated": userdata.escalated,
                "escalation_ref": userdata.escalation_ref,
                "usage": str(usage.get_summary()),
            }
        )
        record = build_call_record(userdata, event_log, usage_summary=str(usage.get_summary()))
        try:
            await bank.post_call_record(record)
            log.info("call_record_posted", outcome=record.outcome, tools=record.tools_used)
        except BankAPIError as exc:
            log.warning("call_record_post_failed", error=str(exc))
        await bank.aclose()

    ctx.add_shutdown_callback(_shutdown)

    log.info("session_starting", llm_provider=settings.llm_provider, llm=settings.llm_model)
    await session.start(agent=IdentityAgent(), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(server)
