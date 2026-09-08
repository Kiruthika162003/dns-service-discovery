from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.tombstones import TombstoneStore


def store() -> TombstoneStore:
    built = TombstoneStore()
    built.register("billing/inst-1", version=5)
    return built


class TestBurial:
    def test_deletion_is_a_record_of_absence(self):
        chosen = store()
        verdict = chosen.deregister(
            "billing/inst-1", version=6, now=100
        )
        assert "record of absence" in verdict
        assert "billing/inst-1" not in chosen.living

    def test_burying_nothing_digs_a_pointless_hole(self):
        with pytest.raises(Invalid) as caught:
            store().deregister("ghost", version=1, now=0)
        assert "digs a hole for no reason" in str(caught.value)

    def test_an_old_deletion_cannot_bury_a_newer_life(self):
        chosen = store()
        with pytest.raises(Invalid):
            chosen.deregister("billing/inst-1", version=4, now=0)


class TestResurrectionDefense:
    def test_the_old_rumor_bounces_off_the_grave(self):
        chosen = store()
        chosen.deregister("billing/inst-1", version=6, now=100)
        verdict = chosen.merge_rumor("billing/inst-1", version=5)
        assert "bounced off the grave marker" in verdict
        assert "the ghost does not walk" in verdict
        assert "billing/inst-1" not in chosen.living
        assert chosen.resurrections_blocked == 1

    def test_a_genuinely_newer_life_reopens_the_grave(self):
        chosen = store()
        chosen.deregister("billing/inst-1", version=6, now=100)
        verdict = chosen.merge_rumor("billing/inst-1", version=7)
        assert "registered at version 7" in verdict
        assert "billing/inst-1" in chosen.living
        assert "billing/inst-1" not in chosen.graves


class TestReaping:
    def test_graves_hold_until_the_horizon(self):
        chosen = store()
        chosen.deregister("billing/inst-1", version=6, now=100)
        verdict = chosen.reap(now=150)
        assert verdict.startswith("0 grave(s) reaped")
        assert "resurrection permit" in verdict

    def test_past_the_horizon_the_grave_is_reaped(self):
        chosen = store()
        chosen.deregister("billing/inst-1", version=6, now=100)
        verdict = chosen.reap(now=160)
        assert verdict.startswith("1 grave(s) reaped")
        assert chosen.reaped == 1

    def test_the_memory_bill_is_a_line_not_a_surprise(self):
        chosen = store()
        chosen.deregister("billing/inst-1", version=6, now=100)
        chosen.merge_rumor("billing/inst-1", version=5)
        bill = chosen.memory_bill()
        assert (
            "0 living, 1 grave(s) held, 0 reaped, 1 "
            "resurrection(s) blocked"
        ) in bill
