from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.rings import RingRollout


def rollout() -> RingRollout:
    built = RingRollout(change="new-forwarder-config")
    built.add_ring("canary", 5)
    built.add_ring("quarter", 50)
    built.add_ring("fleet", 200)
    return built


class TestTheLadder:
    def test_rings_grow_or_they_are_batches(self):
        built = RingRollout(change="x")
        built.add_ring("canary", 5)
        with pytest.raises(Invalid) as caught:
            built.add_ring("smaller", 3)
        assert "just batches" in str(caught.value)

    def test_no_ring_deploys_before_its_predecessor_bakes(self):
        chosen = rollout()
        chosen.deploy_next(now=0)
        with pytest.raises(Invalid) as caught:
            chosen.deploy_next(now=5)
        assert "urgency is precisely when mistakes ship" in (
            str(caught.value)
        )

    def test_the_baked_ring_earns_the_next(self):
        chosen = rollout()
        chosen.deploy_next(now=0)
        assert "still baking (10 of 30)" in chosen.report_bake(
            "canary", now=10, incident=False
        )
        assert "baked clean" in chosen.report_bake(
            "canary", now=30, incident=False
        )
        verdict = chosen.deploy_next(now=31)
        assert verdict.startswith("quarter (50 resolver(s))")


class TestTheRollback:
    def test_an_incident_rolls_back_everywhere(self):
        chosen = rollout()
        chosen.deploy_next(now=0)
        verdict = chosen.report_bake(
            "canary", now=10, incident=True
        )
        assert verdict.startswith("ROLLBACK everywhere")
        assert "more zeros" in verdict
        with pytest.raises(Invalid):
            chosen.deploy_next(now=20)

    def test_the_ledger_credits_the_rings_for_the_catch(self):
        chosen = rollout()
        chosen.deploy_next(now=0)
        chosen.report_bake("canary", now=10, incident=True)
        ledger = chosen.rollout_ledger(now=20)
        assert "caught it at 5 resolver(s)" in ledger


class TestTheCostOfCaution:
    def test_the_complete_rollout_prices_its_patience(self):
        chosen = rollout()
        now = 0
        for ring_name in ("canary", "quarter", "fleet"):
            chosen.deploy_next(now=now)
            now += 30
            chosen.report_bake(ring_name, now=now, incident=False)
        ledger = chosen.rollout_ledger(now=now)
        assert "complete in 90 tick(s)" in ledger
        assert "a number, not a myth to resent" in ledger
