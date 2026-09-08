from __future__ import annotations

import pytest

from beacon.errors import Refused
from beacon.semaphore import Semaphore


class TestAcquire:
    def test_permits_are_granted_up_to_the_limit(self):
        sem = Semaphore(permits=2)
        sem.acquire("a", now=0, lease=10)
        sem.acquire("b", now=0, lease=10)
        assert sem.available(now=0) == 0

    def test_over_the_limit_is_refused(self):
        sem = Semaphore(permits=1)
        sem.acquire("a", now=0, lease=10)
        with pytest.raises(Refused):
            sem.acquire("b", now=0, lease=10)


class TestLeaseExpiry:
    def test_a_lapsed_lease_returns_the_permit(self):
        sem = Semaphore(permits=1)
        sem.acquire("crashed", now=0, lease=10)
        # a later acquire past the lease reclaims the permit
        sem.acquire("newcomer", now=20, lease=10)
        assert "newcomer" in sem.held
        assert "crashed" not in sem.held

    def test_renewing_keeps_the_permit(self):
        sem = Semaphore(permits=1)
        sem.acquire("a", now=0, lease=10)
        sem.renew("a", now=8, lease=10)
        assert sem.available(now=12) == 0  # still held after renew

    def test_renewing_a_lapsed_holder_is_refused(self):
        sem = Semaphore(permits=1)
        sem.acquire("a", now=0, lease=10)
        with pytest.raises(Refused) as caught:
            sem.renew("a", now=20, lease=10)
        assert "reclaimed while it was slow" in str(caught.value)


class TestRelease:
    def test_release_frees_the_permit(self):
        sem = Semaphore(permits=1)
        sem.acquire("a", now=0, lease=10)
        sem.release("a")
        assert sem.available(now=0) == 1
