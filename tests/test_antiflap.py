from __future__ import annotations

import pytest

from beacon.antiflap import FlapDamper
from beacon.errors import Invalid


class TestConstruction:
    def test_reuse_at_or_above_suppress_is_refused(self):
        with pytest.raises(Invalid) as caught:
            FlapDamper(suppress_threshold=3.0, reuse_threshold=3.0)
        assert "erase the hysteresis" in str(caught.value)

    def test_a_nonpositive_half_life_is_refused(self):
        with pytest.raises(Invalid):
            FlapDamper(half_life=0)


class TestSuppression:
    def test_a_few_flaps_suppress_the_route(self):
        damper = FlapDamper(
            penalty_per_flap=1.0, suppress_threshold=3.0
        )
        damper.flap()
        damper.flap()
        assert damper.usable()
        damper.flap()
        assert not damper.usable()

    def test_the_penalty_decays_over_time(self):
        damper = FlapDamper(
            penalty_per_flap=1.0,
            suppress_threshold=3.0,
            reuse_threshold=1.5,
            half_life=15.0,
        )
        for _ in range(3):
            damper.flap()
        assert not damper.usable()
        damper.decay(30.0)  # 3.0 -> 0.75, below reuse
        assert damper.usable()


class TestHysteresis:
    def test_dropping_just_below_suppress_does_not_reuse(self):
        damper = FlapDamper(
            penalty_per_flap=1.0,
            suppress_threshold=3.0,
            reuse_threshold=1.5,
            half_life=15.0,
        )
        for _ in range(3):
            damper.flap()
        # decay a little: 3.0 -> ~2.6, still above reuse 1.5
        damper.decay(3.0)
        assert not damper.usable()
