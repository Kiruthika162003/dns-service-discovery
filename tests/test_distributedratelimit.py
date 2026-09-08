from __future__ import annotations

import pytest

from beacon.distributedratelimit import DistributedRateLimiter
from beacon.errors import Invalid, Refused


class TestConstruction:
    def test_the_budget_splits_across_servers(self):
        limiter = DistributedRateLimiter(global_budget=100, servers=["a", "b"])
        assert limiter.remaining_local("a") == 50
        assert limiter.remaining_local("b") == 50

    def test_a_zero_budget_is_refused(self):
        with pytest.raises(Invalid):
            DistributedRateLimiter(0, ["a"])


class TestLocalSpend:
    def test_a_server_spends_its_slice_without_coordination(self):
        limiter = DistributedRateLimiter(4, ["a", "b"])
        limiter.spend("a")
        limiter.spend("a")
        assert limiter.remaining_local("a") == 0

    def test_a_drained_server_is_refused_until_reconcile(self):
        limiter = DistributedRateLimiter(2, ["a", "b"])
        limiter.spend("a")
        with pytest.raises(Refused) as caught:
            limiter.spend("a")
        assert "waits for the\nnext reconcile" in caught.value.args[0] or (
            "waits for the next reconcile" in str(caught.value)
        )


class TestReconcile:
    def test_reconcile_pools_and_redistributes_the_remainder(self):
        limiter = DistributedRateLimiter(10, ["a", "b"])
        # a spends heavily, b sits idle
        for _ in range(5):
            limiter.spend("a")
        assert limiter.remaining_local("a") == 0
        assert limiter.remaining_local("b") == 5
        limiter.reconcile()  # pool 5, split evenly
        assert limiter.remaining_local("a") == 3  # 2 + remainder 1
        assert limiter.remaining_local("b") == 2
