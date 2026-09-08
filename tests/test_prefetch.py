from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.prefetch import PrefetchPlanner


def planner() -> PrefetchPlanner:
    built = PrefetchPlanner()
    built.admit("www.example.com.", expires_at=100)
    built.admit("rare.example.com.", expires_at=100)
    for _ in range(4):
        built.note_ask("www.example.com.")
    built.note_ask("rare.example.com.")
    return built


class TestEarning:
    def test_only_the_popular_come_due(self):
        chosen = planner()
        assert chosen.due_for_prefetch(now=92) == [
            "www.example.com."
        ]

    def test_too_early_is_not_due(self):
        assert planner().due_for_prefetch(now=80) == []

    def test_the_unpopular_cannot_be_prefetched(self):
        chosen = planner()
        with pytest.raises(Invalid) as caught:
            chosen.prefetch(
                "rare.example.com.", new_expiry=200, now=92
            )
        assert "doubles load for nobody" in str(caught.value)

    def test_a_stranger_cannot_be_asked_about(self):
        with pytest.raises(Invalid):
            planner().note_ask("ghost.example.com.")


class TestSettling:
    def test_the_unlucky_client_never_existed(self):
        chosen = planner()
        chosen.prefetch("www.example.com.", new_expiry=400, now=92)
        verdict = chosen.settle_expiry(
            "www.example.com.", asked_after=True
        )
        assert "never existed" in verdict
        assert chosen.cold_misses_avoided == 1

    def test_the_cold_turn_is_freight_for_nothing(self):
        chosen = planner()
        chosen.prefetch("www.example.com.", new_expiry=400, now=92)
        verdict = chosen.settle_expiry(
            "www.example.com.", asked_after=False
        )
        assert "freight for nothing" in verdict
        assert chosen.wasted_refreshes == 1

    def test_unpopular_names_expire_unwatched(self):
        verdict = planner().settle_expiry(
            "rare.example.com.", asked_after=False
        )
        assert "as unpopular names do" in verdict

    def test_the_ledger_prices_both_sides(self):
        chosen = planner()
        chosen.prefetch("www.example.com.", new_expiry=400, now=92)
        chosen.settle_expiry("www.example.com.", asked_after=True)
        ledger = chosen.ledger()
        assert "1 cold miss(es) avoided, 0 wasted" in ledger
        assert "honest input" in ledger
