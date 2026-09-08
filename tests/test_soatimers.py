from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.soatimers import SoaTimers


def timers() -> SoaTimers:
    return SoaTimers(refresh=3600, retry=600, expire=604800)


class TestConstruction:
    def test_expire_must_exceed_refresh(self):
        with pytest.raises(Invalid) as caught:
            SoaTimers(refresh=3600, retry=600, expire=1800)
        assert "can never serve at all" in str(caught.value)

    def test_retry_must_not_exceed_refresh(self):
        with pytest.raises(Invalid):
            SoaTimers(refresh=600, retry=3600, expire=604800)


class TestServing:
    def test_a_recently_refreshed_zone_serves(self):
        assert timers().serving(now=100000, last_success=99000)

    def test_a_zone_past_expire_stops_serving(self):
        assert timers().expired(now=700000, last_success=0)

    def test_stale_but_recent_beats_an_outage(self):
        # a day without refresh, but expire is a week
        assert timers().serving(now=86400, last_success=0)


class TestChecks:
    def test_a_failing_refresh_drops_to_retry(self):
        assert timers().next_check(refresh_failing=True) == 600

    def test_a_healthy_refresh_uses_the_refresh_interval(self):
        assert timers().next_check(refresh_failing=False) == 3600
