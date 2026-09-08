from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.panicthreshold import PanicPolicy


class TestConstruction:
    def test_a_threshold_outside_zero_to_one_is_refused(self):
        with pytest.raises(Invalid):
            PanicPolicy(threshold=1.5)


class TestPanicDecision:
    def test_a_mostly_healthy_pool_is_not_in_panic(self):
        policy = PanicPolicy(threshold=0.5)
        assert not policy.in_panic(healthy=8, total=10)

    def test_a_mostly_dead_pool_is_in_panic(self):
        policy = PanicPolicy(threshold=0.5)
        assert policy.in_panic(healthy=2, total=10)

    def test_an_empty_pool_is_refused(self):
        with pytest.raises(Invalid):
            PanicPolicy().in_panic(0, 0)


class TestRouting:
    def test_normal_routing_uses_only_healthy_hosts(self):
        policy = PanicPolicy(threshold=0.5)
        healthy = ["a", "b", "c", "d", "e", "f", "g", "h"]
        allh = [*healthy, "x", "y"]
        assert policy.route_pool(healthy, allh) == healthy

    def test_panic_routing_uses_every_host(self):
        policy = PanicPolicy(threshold=0.5)
        healthy = ["a", "b"]
        allh = [*healthy, "c", "d", "e", "f", "g", "h", "i", "j"]
        assert policy.route_pool(healthy, allh) == allh

    def test_the_explanation_names_the_reason(self):
        policy = PanicPolicy(threshold=0.5)
        panic = policy.explain(2, 10)
        assert panic.startswith("panic:")
        assert "filtering" in panic
        assert "only healthy hosts" in policy.explain(9, 10)
