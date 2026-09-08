from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.signaturewindow import Signature, plan_lifetime


class TestValidity:
    def test_a_signature_valid_now_verifies(self):
        assert Signature(100, 200).valid_at(150)

    def test_before_inception_fails(self):
        assert not Signature(100, 200).valid_at(90)

    def test_clock_skew_widens_the_window_both_ways(self):
        sig = Signature(100, 200)
        assert sig.valid_at(95, clock_skew=10)
        assert sig.valid_at(205, clock_skew=10)

    def test_a_zero_width_window_is_refused(self):
        with pytest.raises(Invalid) as caught:
            Signature(200, 200)
        assert "valid for no instant" in str(caught.value)


class TestRefresh:
    def test_refresh_is_due_inside_the_resign_interval(self):
        sig = Signature(0, 1000)
        assert sig.refresh_due(now=900, resign_interval=200)
        assert not sig.refresh_due(now=700, resign_interval=200)

    def test_runway_counts_down_to_the_refresh_point(self):
        sig = Signature(0, 1000)
        assert sig.runway(now=700, resign_interval=200) == 100


class TestPlanning:
    def test_a_lifetime_longer_than_the_interval_has_runway(self):
        assert plan_lifetime(resign_interval=200, lifetime=1000) == 800

    def test_a_lifetime_not_longer_than_the_interval_is_refused(
        self,
    ):
        with pytest.raises(Invalid) as caught:
            plan_lifetime(resign_interval=200, lifetime=200)
        assert "expires the zone into bogus" in str(caught.value)
