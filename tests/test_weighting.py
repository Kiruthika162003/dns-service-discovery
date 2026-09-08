from __future__ import annotations

import pytest

from beacon.errors import Invalid, Missing
from beacon.weighting import (
    Endpoint,
    build_wheel,
    locality_order,
    pick,
    share_report,
)

HEAVY = Endpoint(instance_id="big-1", zone="eu-1", weight=3)
LIGHT = Endpoint(instance_id="small-1", zone="eu-2", weight=1)
DRAINED = Endpoint(instance_id="old-1", zone="eu-1", weight=0)


class TestTheWheel:
    def test_weights_are_exact_not_probable(self):
        wheel = build_wheel([HEAVY, LIGHT])
        assert wheel.count("big-1") == 3
        assert wheel.count("small-1") == 1

    def test_the_rotor_walks_deterministically(self):
        picks = [
            pick([HEAVY, LIGHT], number) for number in range(8)
        ]
        assert picks.count("big-1") == 6
        assert picks.count("small-1") == 2
        assert picks[:4] == picks[4:]

    def test_a_fully_drained_wheel_spins_nobody(self):
        with pytest.raises(Invalid) as caught:
            build_wheel([DRAINED])
        assert "zero spokes spins nobody" in str(caught.value)

    def test_negative_weight_is_nonsense_not_drained(self):
        with pytest.raises(Invalid):
            Endpoint(instance_id="x", zone="z", weight=-1)


class TestLocality:
    def test_local_answers_first_remote_stands_behind(self):
        ordered, note = locality_order(
            [LIGHT, HEAVY], caller_zone="eu-1"
        )
        assert ordered[0].instance_id == "big-1"
        assert "1 local endpoint(s) answer first" in note

    def test_the_preference_is_never_a_fence(self):
        ordered, note = locality_order(
            [LIGHT], caller_zone="eu-1"
        )
        assert ordered[0].instance_id == "small-1"
        assert note.startswith("CROSSED ZONES")
        assert "mystery novel" in note

    def test_drained_everywhere_is_nobody_said_plainly(self):
        with pytest.raises(Missing) as caught:
            locality_order([DRAINED], caller_zone="eu-1")
        assert "said plainly" in str(caught.value)

    def test_the_drained_local_does_not_block_the_crossing(self):
        ordered, note = locality_order(
            [DRAINED, LIGHT], caller_zone="eu-1"
        )
        assert [held.instance_id for held in ordered] == [
            "small-1"
        ]
        assert note.startswith("CROSSED ZONES")


class TestTheShare:
    def test_the_report_shows_exact_shares_and_the_drained(self):
        report = share_report([HEAVY, LIGHT, DRAINED], requests=8)
        assert "big-1: 6 (75%)" in report
        assert "small-1: 2 (25%)" in report
        assert (
            "old-1: drained, discoverable, and taking nobody"
        ) in report

    def test_a_shareless_report_is_refused(self):
        with pytest.raises(Invalid):
            share_report([HEAVY], requests=0)
