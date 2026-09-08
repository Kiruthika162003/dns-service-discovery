from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.slowloris import ConnectionPool


def pool() -> ConnectionPool:
    return ConnectionPool(capacity=5)


class TestProgress:
    def test_progress_resets_the_clock(self):
        chosen = pool()
        chosen.open("c1", "10.0.0.5", now=0)
        verdict = chosen.progress("c1", 100, now=5)
        assert "100 bytes, clock reset" in verdict

    def test_no_progress_keeps_the_clock_running(self):
        chosen = pool()
        chosen.open("c1", "10.0.0.5", now=0)
        verdict = chosen.progress("c1", 0, now=5)
        assert "the clock keeps running" in verdict

    def test_progress_on_a_ghost_is_refused(self):
        with pytest.raises(Invalid):
            pool().progress("ghost", 1, now=0)


class TestReaping:
    def test_the_staller_is_reaped_by_progress_deadline(self):
        chosen = pool()
        chosen.open("c1", "10.0.0.5", now=0)
        reaped = chosen.reap(now=10)
        assert len(reaped) == 1
        assert "the slow-drip signature" in reaped[0]
        assert chosen.stall_reaps == 1

    def test_a_slow_but_advancing_transfer_survives(self):
        chosen = pool()
        chosen.open("c1", "10.0.0.5", now=0)
        chosen.progress("c1", 1, now=8)
        assert chosen.reap(now=15) == []

    def test_a_normal_close_is_not_a_reap(self):
        chosen = pool()
        chosen.open("c1", "10.0.0.5", now=0)
        chosen.close("c1")
        assert chosen.normal_closes == 1
        assert chosen.stall_reaps == 0


class TestTheCaps:
    def test_a_full_pool_names_the_attacker(self):
        chosen = ConnectionPool(capacity=2)
        chosen.open("c1", "a", now=0)
        chosen.open("c2", "b", now=0)
        with pytest.raises(Invalid) as caught:
            chosen.open("c3", "c", now=0)
        assert "not just bad luck" in str(caught.value)

    def test_one_source_cannot_take_the_whole_pool(self):
        chosen = pool()
        for number in range(3):
            chosen.open(f"c{number}", "attacker", now=0)
        verdict = chosen.open("c9", "attacker", now=0)
        assert "may not occupy the whole pool" in verdict
        assert chosen.rejected_for_cap == 1


class TestTheReport:
    def test_the_signature_is_countable(self):
        chosen = pool()
        chosen.open("c1", "10.0.0.5", now=0)
        chosen.reap(now=10)
        report = chosen.defense_report()
        assert "1 stall-reap(s)" in report
        assert "a defense that cannot show it is guessing" in (
            report
        )
