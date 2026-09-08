from __future__ import annotations

import pytest

from beacon.coldstart import ColdStartModel, reloadable
from beacon.errors import Invalid


def model() -> ColdStartModel:
    return ColdStartModel(
        working_set=1000,
        warm_miss_rate=0.05,
        authority_capacity=300,
    )


class TestTheBurst:
    def test_the_cold_burst_is_the_working_set(self):
        assert model().cold_burst() == 1000

    def test_the_warm_load_is_a_fraction(self):
        assert model().warm_load() == 50

    def test_the_cold_burst_can_overwhelm(self):
        assert model().cold_overwhelms()

    def test_an_empty_working_set_is_refused(self):
        with pytest.raises(Invalid):
            ColdStartModel(
                working_set=0,
                warm_miss_rate=0.1,
                authority_capacity=10,
            )


class TestMitigations:
    def test_staggering_spreads_the_peak(self):
        assert model().staggered_peak(5) == 200

    def test_the_report_names_the_fatal_fast_restart(self):
        report = model().strategy_report(5)
        assert "takes the authority down with it" in report
        assert "staggered over 5 wave(s): peak 200, survivable" in (
            report
        )

    def test_a_zero_wave_restart_is_refused(self):
        with pytest.raises(Invalid):
            model().staggered_peak(0)


class TestReloadable:
    def test_a_fresh_entry_reloads(self):
        assert reloadable(age=10, ttl=30)

    def test_an_expired_entry_does_not(self):
        assert not reloadable(age=40, ttl=30)

    def test_a_negative_ttl_is_refused(self):
        with pytest.raises(Invalid):
            reloadable(age=1, ttl=-1)
