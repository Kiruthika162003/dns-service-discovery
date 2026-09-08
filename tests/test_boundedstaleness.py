from __future__ import annotations

import pytest

from beacon.boundedstaleness import staleness, within_bound
from beacon.errors import Invalid


class TestStaleness:
    def test_it_measures_the_lag(self):
        assert staleness(latest_version=10, replica_version=7) == 3

    def test_a_current_replica_has_zero_staleness(self):
        assert staleness(10, 10) == 0

    def test_a_replica_ahead_of_latest_is_refused(self):
        with pytest.raises(Invalid):
            staleness(10, 12)


class TestWithinBound:
    def test_a_replica_inside_the_bound_may_serve(self):
        assert within_bound(latest_version=10, replica_version=7, max_lag=5)

    def test_a_replica_outside_the_bound_may_not(self):
        assert not within_bound(10, 3, max_lag=5)

    def test_the_exact_bound_is_allowed(self):
        assert within_bound(10, 5, max_lag=5)

    def test_a_negative_bound_is_refused(self):
        with pytest.raises(Invalid):
            within_bound(10, 10, max_lag=-1)
