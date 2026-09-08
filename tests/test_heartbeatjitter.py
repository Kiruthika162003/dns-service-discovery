from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.heartbeatjitter import (
    RenewalSchedule,
    jitter_offset,
)

FLEET = [f"inst-{number}" for number in range(1000)]


class TestDeterminism:
    def test_the_offset_is_the_same_slot_forever(self):
        assert jitter_offset("inst-7", 60) == jitter_offset(
            "inst-7", 60
        )

    def test_neighbors_land_in_different_slots(self):
        offsets = {
            jitter_offset(f"inst-{number}", 60)
            for number in range(20)
        }
        assert len(offsets) > 10


class TestTheWallAndTheDrizzle:
    def test_the_metronome_peaks_at_the_whole_fleet(self):
        schedule = RenewalSchedule(interval=60)
        peak, tick = schedule.peak_load(
            FLEET, horizon=180, jittered=False
        )
        assert peak == 1000
        assert tick == 0

    def test_jitter_spreads_the_wall_into_the_teens(self):
        schedule = RenewalSchedule(interval=60)
        peak, _ = schedule.peak_load(
            FLEET, horizon=180, jittered=True
        )
        assert peak == 29

    def test_the_report_carries_both_numbers(self):
        schedule = RenewalSchedule(interval=60)
        report = schedule.smoothing_report(FLEET, horizon=180)
        assert "peaks at 1000 renewal(s) in one tick" in report
        assert "worst tick to 29" in report
        assert "deserved a number and this is it" in report


class TestRefusals:
    def test_a_tiny_interval_leaves_no_room(self):
        with pytest.raises(Invalid):
            RenewalSchedule(interval=1)

    def test_no_fleet_no_peaks(self):
        with pytest.raises(Invalid):
            RenewalSchedule(interval=60).peak_load(
                [], horizon=60, jittered=True
            )
