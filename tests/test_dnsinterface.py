from __future__ import annotations

import pytest

from beacon.dnsinterface import DnsBridge
from beacon.errors import Invalid, Missing


def bridge() -> DnsBridge:
    built = DnsBridge()
    built.note_churn("billing", 0)
    built.note_churn("spot-workers", 8)
    return built


class TestSynthesis:
    def test_passing_instances_become_srv_lines(self):
        records = bridge().synthesize(
            "billing",
            [
                ("b1.node.", 8080, 3, True),
                ("b2.node.", 8080, 1, True),
                ("b3.node.", 8080, 1, False),
            ],
        )
        assert len(records) == 2
        assert records[0].line() == (
            "_svc._tcp.billing. 60 SRV 10 3 8080 b1.node."
        )

    def test_nobody_passing_is_not_an_empty_set(self):
        with pytest.raises(Missing) as caught:
            bridge().synthesize(
                "billing", [("b1.node.", 80, 1, False)]
            )
        assert "would cache the absence" in str(caught.value)


class TestTheTtlChoice:
    def test_stable_services_earn_the_long_ttl(self):
        assert bridge().ttl_for("billing") == 60

    def test_churny_services_get_the_short_one(self):
        assert bridge().ttl_for("spot-workers") == 5

    def test_churn_cannot_be_negative(self):
        with pytest.raises(Invalid):
            DnsBridge().note_churn("x", -1)


class TestTheMismatch:
    def test_the_cost_column_is_priced(self):
        chosen = bridge()
        report = chosen.mismatch_report(
            "spot-workers",
            ttl_used=60,
            deregistrations=8,
            connections_per_tick=10,
        )
        assert (
            "sent roughly 2400 connection(s) to the dead"
        ) in report
        assert "churn says 5 was the honest choice" in report

    def test_the_honest_ttl_carries_no_lecture(self):
        report = bridge().mismatch_report(
            "spot-workers",
            ttl_used=5,
            deregistrations=8,
            connections_per_tick=10,
        )
        assert "honest choice" not in report
        assert "200 connection(s)" in report
