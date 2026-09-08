from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.slowstart import SlowStart


class TestRamp:
    def test_a_fresh_backend_starts_near_zero(self):
        assert SlowStart(window_s=30).ramp_factor(0) == 0.0

    def test_the_ramp_is_linear_across_the_window(self):
        assert SlowStart(window_s=30).ramp_factor(15) == pytest.approx(
            0.5
        )

    def test_past_the_window_it_is_full(self):
        assert SlowStart(window_s=30).ramp_factor(60) == 1.0

    def test_a_zero_window_is_instantly_full(self):
        assert SlowStart(window_s=0).ramp_factor(0) == 1.0


class TestWeight:
    def test_the_effective_weight_scales_by_the_ramp(self):
        assert SlowStart(30).effective_weight(100, 15) == pytest.approx(
            50
        )

    def test_warming_is_true_before_the_window_closes(self):
        chosen = SlowStart(30)
        assert chosen.is_warming(10)
        assert not chosen.is_warming(30)


class TestRefusals:
    def test_a_negative_window_is_refused(self):
        with pytest.raises(Invalid):
            SlowStart(window_s=-1)

    def test_a_negative_age_is_refused(self):
        with pytest.raises(Invalid):
            SlowStart(30).ramp_factor(-5)
