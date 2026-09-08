from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.roundrobin import (
    Rotor,
    behind_a_cache,
    ceiling_report,
)

ADDRESSES = ("10.0.0.1", "10.0.0.2", "10.0.0.3")


class TestNakedRotation:
    def test_the_first_slot_is_shared_exactly(self):
        rotor = Rotor(addresses=ADDRESSES)
        for _ in range(9):
            rotor.answer()
        assert set(rotor.first_slot_counts.values()) == {3}

    def test_the_whole_list_still_arrives(self):
        rotor = Rotor(addresses=ADDRESSES)
        answer = rotor.answer()
        assert sorted(answer) == sorted(ADDRESSES)
        assert rotor.answer()[0] == "10.0.0.2"

    def test_one_address_rotates_into_itself(self):
        with pytest.raises(Invalid):
            Rotor(addresses=("10.0.0.1",))


class TestBehindTheCache:
    def test_a_boundary_aligned_ttl_stays_fair_by_luck(self):
        rotor = Rotor(addresses=ADDRESSES)
        seen = behind_a_cache(rotor, queries=90, ttl=30)
        assert seen == {
            "10.0.0.1": 30,
            "10.0.0.2": 30,
            "10.0.0.3": 30,
        }

    def test_a_long_ttl_hands_one_address_the_window(self):
        rotor = Rotor(addresses=ADDRESSES)
        seen = behind_a_cache(rotor, queries=90, ttl=60)
        assert seen == {"10.0.0.1": 60, "10.0.0.2": 30}
        assert "10.0.0.3" not in seen

    def test_the_ceiling_report_names_the_broken_promise(self):
        report = ceiling_report(ADDRESSES, queries=90, ttl=60)
        assert "naked rotation tops out at 30" in report
        assert "one address takes 60" in report
        assert "the cache quietly breaks the promise" in report

    def test_the_simulation_needs_queries_and_a_ttl(self):
        with pytest.raises(Invalid):
            behind_a_cache(
                Rotor(addresses=ADDRESSES), queries=0, ttl=30
            )
