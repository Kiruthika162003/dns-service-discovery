from __future__ import annotations

import hashlib

import pytest

from beacon.errors import Invalid, Missing
from beacon.hashring import HashRing, movement_on_change

KEYS = [f"key-{number}" for number in range(200)]


def trio() -> HashRing:
    ring = HashRing(vnodes=64)
    for member in ("alpha", "bravo", "charlie"):
        ring.join(member)
    return ring


class TestMovement:
    def test_a_join_moves_a_fifth_not_three_quarters(self):
        ring = trio()
        before = ring.ownership_map(KEYS)
        ring.join("delta")
        moved, share = movement_on_change(
            before, ring.ownership_map(KEYS)
        )
        assert moved == 40
        assert share == pytest.approx(0.20)

    def test_the_modulo_baseline_reshuffles_the_world(self):
        def mod_owner(key: str, count: int) -> int:
            digest = hashlib.sha256(key.encode()).hexdigest()
            return int(digest[:8], 16) % count

        moved = sum(
            1
            for key in KEYS
            if mod_owner(key, 3) != mod_owner(key, 4)
        )
        assert moved == 153

    def test_a_leave_moves_only_the_leavers_arc(self):
        ring = trio()
        ring.join("delta")
        before = ring.ownership_map(KEYS)
        ring.leave("bravo")
        moved, _ = movement_on_change(
            before, ring.ownership_map(KEYS)
        )
        assert moved == 36
        for key, owner in before.items():
            if owner != "bravo":
                assert ring.owner_of(key) == owner

    def test_different_key_sets_cannot_be_compared(self):
        with pytest.raises(Invalid):
            movement_on_change({"a": "x"}, {"b": "x"})


class TestBalance:
    def test_one_vnode_is_a_lottery(self):
        ring = HashRing(vnodes=1)
        for member in ("alpha", "bravo", "charlie"):
            ring.join(member)
        report = ring.spread_report(KEYS)
        assert "heaviest 119, lightest 14" in report

    def test_sixty_four_vnodes_average_the_luck_out(self):
        report = trio().spread_report(KEYS)
        assert "heaviest 80, lightest 59" in report
        assert "balance is a number, not a claim" in report


class TestMembership:
    def test_double_joins_and_ghost_leaves_are_refused(self):
        ring = trio()
        with pytest.raises(Invalid):
            ring.join("alpha")
        with pytest.raises(Missing):
            ring.leave("zulu")

    def test_an_empty_ring_owns_nothing(self):
        with pytest.raises(Missing):
            HashRing().owner_of("key-1")
