"""Unit tests for per-turn latency aggregation (pure part of LatencyCollector)."""

from bankagent_agent.latency import LatencyCollector


def _add_turn(c: LatencyCollector, speech_id: str, eou: float, ttft: float, ttfb: float) -> None:
    c.add(speech_id, "eou", eou)
    c.add(speech_id, "ttft", ttft)
    c.add(speech_id, "ttfb", ttfb)


class TestSummary:
    def test_no_complete_turns_is_none(self) -> None:
        c = LatencyCollector()
        assert c.summary() is None
        c.add("s1", "ttft", 0.5)  # LLM-only turn (e.g. text chat)
        assert c.summary() is None

    def test_joins_parts_by_speech_id(self) -> None:
        c = LatencyCollector()
        _add_turn(c, "s1", eou=0.3, ttft=0.5, ttfb=0.2)
        _add_turn(c, "s2", eou=0.5, ttft=0.7, ttfb=0.4)
        c.add("s3", "eou", 0.4)  # incomplete: no LLM/TTS parts

        stats = c.summary()
        assert stats is not None
        assert stats.turns == 2
        assert stats.eou_median_s == 0.4
        assert stats.llm_ttft_median_s == 0.6
        assert stats.tts_ttfb_median_s == 0.3
        assert stats.total_median_s == 1.3  # median of [1.0, 1.6]
        assert stats.total_p95_s == 1.6

    def test_unmeasured_and_duplicate_samples(self) -> None:
        c = LatencyCollector()
        c.add("s1", "ttft", -1.0)  # not measured - ignored
        _add_turn(c, "s1", eou=0.3, ttft=0.5, ttfb=0.2)
        c.add("s1", "ttft", 9.9)  # retry within same speech turn - first sample kept

        stats = c.summary()
        assert stats is not None
        assert stats.turns == 1
        assert stats.llm_ttft_median_s == 0.5
        assert stats.total_median_s == 1.0

    def test_p95_excludes_the_worst_five_percent(self) -> None:
        c = LatencyCollector()
        for i in range(19):
            _add_turn(c, f"s{i}", eou=0.3, ttft=0.5, ttfb=0.2)
        _add_turn(c, "slow", eou=1.0, ttft=2.0, ttfb=1.0)

        stats = c.summary()
        assert stats is not None
        assert stats.total_median_s == 1.0
        # 1 of 20 samples is exactly the worst 5% - p95 sits below the outlier.
        assert stats.total_p95_s == 1.0

    def test_p95_catches_a_slow_tail_that_is_more_than_five_percent(self) -> None:
        c = LatencyCollector()
        for i in range(8):
            _add_turn(c, f"fast{i}", eou=0.3, ttft=0.5, ttfb=0.2)
        for i in range(2):
            _add_turn(c, f"slow{i}", eou=1.0, ttft=2.0, ttfb=1.0)

        stats = c.summary()
        assert stats is not None
        assert stats.total_p95_s == 4.0
