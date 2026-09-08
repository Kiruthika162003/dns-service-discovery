from __future__ import annotations

import pytest

from beacon.capacity import CapacityRouter
from beacon.errors import Invalid


def router() -> CapacityRouter:
    built = CapacityRouter()
    built.add("big", 60)
    built.add("small", 40)
    return built


class TestTheCorrection:
    def test_load_eases_the_effective_weight_down(self):
        chosen = router()
        verdict = chosen.report_load("big", 0.9)
        assert "eased toward 6" in verdict
        assert chosen.backends["big"].effective_weight == 33.0

    def test_the_static_split_ignores_load(self):
        chosen = router()
        chosen.report_load("big", 0.9)
        assert chosen.split(use_load=False) == {
            "big": 0.6,
            "small": 0.4,
        }

    def test_the_corrected_split_drains_the_busy_backend(self):
        chosen = router()
        chosen.report_load("big", 0.9)
        corrected = chosen.split(use_load=True)
        assert corrected["big"] < 0.5
        assert corrected["small"] > 0.5


class TestDampingAndSafety:
    def test_the_correction_is_damped_not_instant(self):
        chosen = router()
        chosen.report_load("big", 1.0)
        assert chosen.backends["big"].effective_weight == 30.0

    def test_a_zero_static_weight_is_drained_not_routed(self):
        with pytest.raises(Invalid):
            router().add("dead", 0)

    def test_load_is_a_fraction(self):
        with pytest.raises(Invalid):
            router().report_load("big", 1.5)


class TestTheReport:
    def test_the_report_contrasts_the_two_splits(self):
        chosen = router()
        chosen.report_load("big", 0.9)
        report = chosen.correction_report()
        assert "big: 60% -> 45%" in report
        assert "small: 40% -> 55%" in report
        assert "measurement says is full" in report
