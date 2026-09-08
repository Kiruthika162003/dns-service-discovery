from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.leaseexpiry import LeaseRegistry


class TestConstruction:
    def test_a_heartbeat_too_close_to_the_ttl_is_refused(self):
        with pytest.raises(Invalid) as caught:
            LeaseRegistry(ttl=30, heartbeat_interval=20)
        assert "single lost packet" in str(caught.value)

    def test_a_safe_ratio_is_accepted(self):
        registry = LeaseRegistry(ttl=30, heartbeat_interval=10)
        assert registry.ttl == 30


class TestLeaseLifecycle:
    def test_a_fresh_registration_is_alive(self):
        registry = LeaseRegistry(30, 10)
        registry.register("svc-1", now=0)
        assert registry.alive("svc-1", now=20)

    def test_a_lease_expires_past_the_ttl(self):
        registry = LeaseRegistry(30, 10)
        registry.register("svc-1", now=0)
        assert not registry.alive("svc-1", now=40)

    def test_a_heartbeat_renews_the_lease(self):
        registry = LeaseRegistry(30, 10)
        registry.register("svc-1", now=0)
        registry.heartbeat("svc-1", now=25)
        assert registry.alive("svc-1", now=50)


class TestSweep:
    def test_the_sweep_removes_only_the_expired(self):
        registry = LeaseRegistry(30, 10)
        registry.register("fresh", now=20)
        registry.register("stale", now=0)
        assert registry.sweep(now=40) == ["stale"]
        assert registry.alive("fresh", now=40)

    def test_a_heartbeat_for_a_ghost_is_refused(self):
        registry = LeaseRegistry(30, 10)
        with pytest.raises(Invalid) as caught:
            registry.heartbeat("never-registered", now=5)
        assert "resurrect a swept ghost" in str(caught.value)
