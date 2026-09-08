from __future__ import annotations

import pytest

from beacon.errors import Invalid, Refused
from beacon.quota import Quota


class TestConstruction:
    def test_a_nonpositive_limit_is_refused(self):
        with pytest.raises(Invalid):
            Quota(limit=0, window=86400)

    def test_a_nonpositive_window_is_refused(self):
        with pytest.raises(Invalid):
            Quota(limit=100, window=0)


class TestConsumption:
    def test_consuming_within_the_limit_returns_the_remainder(self):
        quota = Quota(limit=100, window=86400)
        assert quota.consume(30, now=0) == 70
        assert quota.consume(20, now=10) == 50

    def test_exceeding_the_quota_is_refused(self):
        quota = Quota(limit=100, window=86400)
        quota.consume(90, now=0)
        with pytest.raises(Refused) as caught:
            quota.consume(20, now=10)
        assert "the day's" in str(caught.value)


class TestWindowRoll:
    def test_the_window_resets_after_its_period(self):
        quota = Quota(limit=100, window=86400)
        quota.consume(100, now=0)
        assert quota.remaining(now=0) == 0
        # a day later the window rolls over
        assert quota.remaining(now=86400) == 100
        assert quota.consume(50, now=86400) == 50
