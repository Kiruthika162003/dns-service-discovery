from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.probes import Watchtower


def tower() -> Watchtower:
    built = Watchtower()
    built.add_probe(
        "www.shop.example.", "192.0.2.10", view="outside"
    )
    return built


class TestGrading:
    def test_the_expected_answer_resets_the_streak(self):
        chosen = tower()
        chosen.observe(
            "www.shop.example.", "outside", "203.0.113.1", 10
        )
        verdict = chosen.observe(
            "www.shop.example.", "outside", "192.0.2.10", 10
        )
        assert "as expected in 10" in verdict
        assert chosen.probes[
            "www.shop.example.@outside"
        ].bad_streak == 0

    def test_wrong_is_the_gravest_kind(self):
        verdict = tower().observe(
            "www.shop.example.", "outside", "203.0.113.66", 10
        )
        assert "WRONG, the gravest" in verdict
        assert "worse than serving none" in verdict

    def test_slow_and_missing_are_their_own_kinds(self):
        chosen = tower()
        slow = chosen.observe(
            "www.shop.example.", "outside", "192.0.2.10", 90
        )
        assert "SLOW at 90" in slow
        missing = chosen.observe(
            "www.shop.example.", "outside", None, 10
        )
        assert "MISSING" in missing


class TestThePagerRule:
    def test_one_bad_probe_logs_and_three_page(self):
        chosen = tower()
        for _ in range(2):
            verdict = chosen.observe(
                "www.shop.example.", "outside", None, 10
            )
            assert "logged" in verdict
        verdict = chosen.observe(
            "www.shop.example.", "outside", None, 10
        )
        assert "PAGING" in verdict
        assert chosen.pages_sent == 1
        assert chosen.logged_only == 2

    def test_unwatched_probes_cannot_be_observed(self):
        with pytest.raises(Invalid):
            tower().observe("ghost.", "outside", None, 1)

    def test_double_watching_is_refused(self):
        chosen = tower()
        with pytest.raises(Invalid):
            chosen.add_probe(
                "www.shop.example.", "x", view="outside"
            )


class TestCoverage:
    def test_the_unwatched_zone_reports_to_nobody(self):
        report = tower().coverage_report(
            ["shop.example.", "corp.example."]
        )
        assert "1 unwatched zone(s)" in report
        assert "corp.example." in report
        assert "report to nobody" in report

    def test_full_coverage_has_somewhere_to_report(self):
        assert "all watched" in tower().coverage_report(
            ["shop.example."]
        )
