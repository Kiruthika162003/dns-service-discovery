from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.outlierdetect import OutlierEjector


def fleet(rates: dict[str, float]) -> OutlierEjector:
    ejector = OutlierEjector()
    for instance, rate in rates.items():
        ejector.observe(instance, rate)
    return ejector


class TestStandingApart:
    def test_the_one_rotten_instance_is_ejected(self):
        ejector = fleet(
            {"a": 0.01, "b": 0.02, "c": 0.01, "d": 0.30}
        )
        verdicts = ejector.evaluate()
        assert any(
            "d ejected at 30%" in line for line in verdicts
        )
        assert "d" in ejector.ejected

    def test_the_fleet_wide_burn_pages_the_deploy(self):
        ejector = fleet({"a": 0.25, "b": 0.30, "c": 0.28})
        verdicts = ejector.evaluate()
        assert verdicts == [
            "nobody stands apart; a fleet-wide burn pages "
            "the deploy, not the ejector"
        ]

    def test_a_clean_crowd_with_one_mild_case_keeps_it(self):
        ejector = fleet(
            {"a": 0.01, "b": 0.02, "c": 0.01, "d": 0.02}
        )
        verdicts = ejector.evaluate()
        assert "nobody stands apart" in verdicts[0]


class TestTheCap:
    def test_the_detector_cannot_eject_everyone(self):
        ejector = fleet(
            {
                "a": 0.30,
                "b": 0.40,
                "c": 0.01,
                "d": 0.01,
                "e": 0.01,
                "f": 0.01,
            }
        )
        verdicts = ejector.evaluate()
        assert len(ejector.ejected) == 2
        joined = "\n".join(verdicts)
        assert "cause the outage it guards against" not in joined

    def test_when_the_cap_binds_the_sick_stay_named(self):
        ejector = fleet(
            {
                "a": 0.50,
                "b": 0.45,
                "c": 0.40,
                "d": 0.01,
                "e": 0.01,
                "f": 0.01,
            }
        )
        verdicts = ejector.evaluate()
        assert len(ejector.ejected) == 2
        assert any(
            "stays IN rotation" in line for line in verdicts
        )
        assert ejector.cap_bound


class TestRefusals:
    def test_rates_live_between_zero_and_one(self):
        with pytest.raises(Invalid):
            OutlierEjector().observe("a", 1.5)

    def test_outliers_need_a_crowd(self):
        ejector = fleet({"a": 0.1, "b": 0.2})
        with pytest.raises(Invalid):
            ejector.evaluate()
