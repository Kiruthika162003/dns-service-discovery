from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.ratelimit import ResponseRateLimiter


def flooded() -> ResponseRateLimiter:
    limiter = ResponseRateLimiter()
    for _ in range(20):
        limiter.respond("203.0.113.0/24")
    return limiter


class TestTheBudget:
    def test_the_first_five_answer_in_full(self):
        limiter = ResponseRateLimiter()
        verdicts = [
            limiter.respond("203.0.113.0/24") for _ in range(5)
        ]
        assert all("full answer" in line for line in verdicts)

    def test_the_excess_mostly_drops(self):
        limiter = flooded()
        assert limiter.answered == 5
        assert limiter.slips_sent == 5

    def test_every_third_excess_slips(self):
        limiter = ResponseRateLimiter()
        for _ in range(5):
            limiter.respond("net")
        verdicts = [limiter.respond("net") for _ in range(6)]
        slips = [v for v in verdicts if "SLIP" in v]
        assert len(slips) == 2
        assert "the whole filter" in slips[0]

    def test_sources_are_limited_separately(self):
        limiter = flooded()
        assert "full answer" in limiter.respond("198.51.100.0/24")

    def test_the_window_resets_the_budget(self):
        limiter = flooded()
        limiter.end_window()
        assert "full answer" in limiter.respond("203.0.113.0/24")


class TestTheReport:
    def test_both_sides_of_the_safety_are_priced(self):
        limiter = flooded()
        report = limiter.amplification_report(floods=15)
        assert "would have shipped 60000 bytes" in report
        assert "5 slip(s) kept the door cracked" in report
        assert "fell from about 66x toward one" in report

    def test_a_floodless_report_is_refused(self):
        with pytest.raises(Invalid):
            ResponseRateLimiter().amplification_report(floods=0)
