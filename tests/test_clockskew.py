from __future__ import annotations

import pytest

from beacon.clockskew import lease_read_safe, safe_until
from beacon.errors import Invalid


class TestSafety:
    def test_a_read_well_inside_the_lease_is_safe(self):
        assert lease_read_safe(lease_expiry=100, now=50, max_skew=10)

    def test_a_read_within_the_skew_margin_is_unsafe(self):
        # now 95, skew 10 -> 105 >= 100, not safe
        assert not lease_read_safe(100, now=95, max_skew=10)

    def test_the_margin_shortens_the_usable_lease(self):
        assert safe_until(lease_expiry=100, max_skew=10) == 90

    def test_exactly_at_the_safe_boundary_is_not_safe(self):
        # now 90, skew 10 -> 100, not strictly less than 100
        assert not lease_read_safe(100, now=90, max_skew=10)


class TestRefusals:
    def test_a_negative_skew_is_refused(self):
        with pytest.raises(Invalid):
            lease_read_safe(100, 50, max_skew=-1)

    def test_safe_until_refuses_negative_skew(self):
        with pytest.raises(Invalid):
            safe_until(100, max_skew=-1)
