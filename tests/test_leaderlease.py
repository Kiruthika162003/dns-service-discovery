from __future__ import annotations

import pytest

from beacon.errors import Fenced, Invalid
from beacon.leaderlease import LeaseStore


def store() -> LeaseStore:
    built = LeaseStore()
    built.acquire("coord-a", now=0)
    return built


class TestTheLease:
    def test_a_held_lease_makes_others_wait(self):
        chosen = store()
        with pytest.raises(Invalid) as caught:
            chosen.acquire("coord-b", now=5)
        assert "coord-b waits its turn" in str(caught.value)

    def test_expiry_transfers_with_a_new_token(self):
        chosen = store()
        verdict = chosen.acquire("coord-b", now=21)
        assert "coord-b leads with token 2" in verdict

    def test_late_renewal_is_a_suggestion_not_a_lease(self):
        chosen = store()
        with pytest.raises(Invalid) as caught:
            chosen.renew("coord-a", now=25)
        assert "a suggestion, not a lease" in str(caught.value)

    def test_renewal_before_expiry_extends(self):
        chosen = store()
        assert chosen.renew("coord-a", now=10) == (
            "coord-a renewed until 30"
        )


class TestTheFence:
    def test_the_current_token_writes(self):
        chosen = store()
        assert chosen.write("coord-a", 1, "state") == (
            "state committed under token 1"
        )

    def test_the_paused_leader_bounces_off_the_fence(self):
        chosen = store()
        chosen.write("coord-a", 1, "state-v1")
        chosen.acquire("coord-b", now=21)
        chosen.write("coord-b", 2, "state-v2")
        with pytest.raises(Fenced) as caught:
            chosen.write("coord-a", 1, "stale")
        assert "bounces off the fence" in str(caught.value)

    def test_the_summary_prices_the_design(self):
        chosen = store()
        chosen.write("coord-a", 1, "v1")
        chosen.acquire("coord-b", now=21)
        chosen.write("coord-b", 2, "v2")
        with pytest.raises(Fenced):
            chosen.write("coord-a", 1, "stale")
        assert "1 split-brain write(s) converted" in (
            chosen.split_brain_summary()
        )

    def test_a_quiet_store_admits_both_readings(self):
        assert "either no split brain or nobody wrote" in (
            store().split_brain_summary()
        )
