from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.multisite import SitePair


def pair() -> SitePair:
    return SitePair(primary="eu-west", backup="us-east")


class TestFailover:
    def test_failover_is_immediate(self):
        chosen = pair()
        verdict = chosen.observe(primary_healthy=False, now=10)
        assert verdict.startswith("FAILOVER to us-east")
        assert "every tick of hesitation" in verdict

    def test_one_site_twice_is_theater(self):
        with pytest.raises(Invalid):
            SitePair(primary="eu", backup="eu")


class TestFailback:
    def failed_over(self) -> SitePair:
        chosen = pair()
        chosen.observe(primary_healthy=False, now=10)
        return chosen

    def test_failback_waits_out_the_damping(self):
        chosen = self.failed_over()
        verdict = chosen.observe(primary_healthy=True, now=15)
        assert "held recovery 0 of 20" in verdict
        verdict = chosen.observe(primary_healthy=True, now=30)
        assert "held recovery 15" in verdict
        assert chosen.serving == "us-east"

    def test_the_held_recovery_earns_the_failback(self):
        chosen = self.failed_over()
        chosen.observe(primary_healthy=True, now=15)
        verdict = chosen.observe(primary_healthy=True, now=35)
        assert verdict.startswith("FAILBACK to eu-west")
        assert "pin traffic forever" in verdict
        assert chosen.serving == "eu-west"

    def test_a_relapse_resets_the_damping_clock(self):
        chosen = self.failed_over()
        chosen.observe(primary_healthy=True, now=15)
        chosen.observe(primary_healthy=False, now=25)
        verdict = chosen.observe(primary_healthy=True, now=30)
        assert "held recovery 0 of 20" in verdict


class TestTheLedger:
    def test_backup_time_is_billed(self):
        chosen = pair()
        chosen.observe(primary_healthy=False, now=10)
        chosen.observe(primary_healthy=False, now=40)
        ledger = chosen.routing_ledger()
        assert "30 tick(s) served from us-east" in ledger

    def test_the_flapping_pair_is_diagnosed(self):
        chosen = pair()
        now = 0
        for _ in range(3):
            now += 5
            chosen.observe(primary_healthy=False, now=now)
            for _ in range(5):
                now += 5
                chosen.observe(primary_healthy=True, now=now)
        ledger = chosen.routing_ledger()
        assert "6 transition(s)" in ledger
        assert "routing costume" in ledger
