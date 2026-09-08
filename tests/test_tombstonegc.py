from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.tombstonegc import may_collect, resurrection_risk_if_collected


class TestMayCollect:
    def test_a_tombstone_past_the_grace_is_collectible(self):
        assert may_collect(tombstone_age=100, grace_period=60)

    def test_a_young_tombstone_is_not(self):
        assert not may_collect(tombstone_age=30, grace_period=60)

    def test_exactly_at_the_grace_is_collectible(self):
        assert may_collect(60, 60)

    def test_a_negative_age_is_refused(self):
        with pytest.raises(Invalid):
            may_collect(-1, 60)


class TestResurrection:
    def test_collecting_before_the_grace_risks_resurrection(self):
        assert resurrection_risk_if_collected(tombstone_age=30, grace_period=60)

    def test_collecting_after_the_grace_is_safe(self):
        assert not resurrection_risk_if_collected(100, 60)
