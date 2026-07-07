"""Collects per-turn conversational latency from LiveKit's metrics events.

What a caller experiences as "how fast it answers" is, per turn:

    end-of-utterance delay  (turn detector deciding the caller finished)
  + LLM time-to-first-token
  + TTS time-to-first-byte

The three parts arrive as separate metrics events sharing a ``speech_id``;
this collector joins them and summarizes complete turns for the call record.
Aggregation is pure and unit-tested; only ``collect`` touches LiveKit types.
"""

from __future__ import annotations

import statistics

from livekit.agents.metrics import AgentMetrics, EOUMetrics, LLMMetrics, TTSMetrics

from bankagent_shared.models import CallLatencyStats


class LatencyCollector:
    def __init__(self) -> None:
        self._turns: dict[str, dict[str, float]] = {}

    def collect(self, m: AgentMetrics) -> None:
        if isinstance(m, EOUMetrics) and m.speech_id:
            self.add(m.speech_id, "eou", m.end_of_utterance_delay)
        elif isinstance(m, LLMMetrics) and m.speech_id:
            self.add(m.speech_id, "ttft", m.ttft)
        elif isinstance(m, TTSMetrics) and m.speech_id:
            self.add(m.speech_id, "ttfb", m.ttfb)

    def add(self, speech_id: str, part: str, seconds: float) -> None:
        if seconds <= 0:  # -1 = not measured (e.g. non-streaming fallback)
            return
        # Keep the first sample per part: retries/continuations of the same
        # speech turn should not overwrite the latency the caller experienced.
        self._turns.setdefault(speech_id, {}).setdefault(part, seconds)

    def summary(self) -> CallLatencyStats | None:
        complete = [t for t in self._turns.values() if {"eou", "ttft", "ttfb"} <= t.keys()]
        if not complete:
            return None
        totals = sorted(t["eou"] + t["ttft"] + t["ttfb"] for t in complete)
        p95_index = max(0, round(0.95 * (len(totals) - 1)))
        return CallLatencyStats(
            turns=len(complete),
            eou_median_s=round(statistics.median(t["eou"] for t in complete), 3),
            llm_ttft_median_s=round(statistics.median(t["ttft"] for t in complete), 3),
            tts_ttfb_median_s=round(statistics.median(t["ttfb"] for t in complete), 3),
            total_median_s=round(statistics.median(totals), 3),
            total_p95_s=round(totals[p95_index], 3),
        )
