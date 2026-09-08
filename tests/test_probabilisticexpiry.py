from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.probabilisticexpiry import should_refresh


class TestWindow:
    def test_far_from_expiry_almost_never_refreshes(self):
        # now 0, expiry 100, small early window -> no refresh
        assert not should_refresh(
            now=0, expiry=100, recompute_cost=1, beta=1, draw=0.5
        )

    def test_at_expiry_it_refreshes(self):
        assert should_refresh(
            now=100, expiry=100, recompute_cost=1, beta=1, draw=0.5
        )

    def test_a_costly_entry_refreshes_earlier(self):
        # large recompute cost widens the early window
        assert should_refresh(
            now=90, expiry=100, recompute_cost=50, beta=1, draw=0.5
        )

    def test_a_cheap_entry_does_not_yet(self):
        assert not should_refresh(
            now=90, expiry=100, recompute_cost=0.1, beta=1, draw=0.9
        )


class TestRefusals:
    def test_a_zero_draw_is_refused(self):
        with pytest.raises(Invalid) as caught:
            should_refresh(90, 100, 1, 1, draw=0.0)
        assert "undefined at zero" in str(caught.value)

    def test_a_negative_cost_is_refused(self):
        with pytest.raises(Invalid):
            should_refresh(90, 100, -1, 1, draw=0.5)
