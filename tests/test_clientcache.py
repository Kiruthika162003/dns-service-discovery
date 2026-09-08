from __future__ import annotations

import pytest

from beacon.clientcache import ClientCache
from beacon.errors import Expired, Invalid, Missing


def cache() -> ClientCache:
    built = ClientCache()
    built.store(
        "billing", ("10.0.0.1:80", "10.0.0.2:80"), now=0
    )
    return built


class TestTheSteps:
    def test_fresh_serves_normally(self):
        assert cache().serve("billing", now=20) == (
            "billing: 2 instance(s), fresh"
        )

    def test_aging_serves_with_the_mark(self):
        verdict = cache().serve("billing", now=100)
        assert "[STALE, 100 tick(s) old]" in verdict
        assert "declared steps, not a cliff" in verdict

    def test_past_the_ceiling_the_call_fails_honestly(self):
        with pytest.raises(Expired) as caught:
            cache().serve("billing", now=300)
        assert "old enough to be strangers" in str(caught.value)

    def test_no_yesterday_no_fallback(self):
        with pytest.raises(Missing) as caught:
            cache().serve("search", now=10)
        assert "no yesterday to fall back on" in str(
            caught.value
        )

    def test_absences_are_not_cached(self):
        with pytest.raises(Invalid):
            ClientCache().store("billing", (), now=0)


class TestTheBackoff:
    def test_failures_double_the_wait_to_a_cap(self):
        chosen = cache()
        waits = []
        now = 10
        for _ in range(8):
            verdict = chosen.registry_failed(now)
            waits.append(
                int(verdict.split(" ")[2])
            )
        assert waits == [1, 2, 4, 8, 16, 32, 64, 64]

    def test_the_polite_client_counts_what_it_did_not_send(self):
        chosen = cache()
        chosen.registry_failed(now=10)
        chosen.registry_failed(now=11)
        assert not chosen.may_query_registry(now=12)
        assert chosen.may_query_registry(now=13)
        assert "1 query(ies) not sent" in (
            chosen.politeness_ledger()
        )

    def test_a_success_resets_the_backoff(self):
        chosen = cache()
        for _ in range(5):
            chosen.registry_failed(now=10)
        chosen.store("billing", ("10.0.0.9:80",), now=50)
        assert chosen.backoff == 1
