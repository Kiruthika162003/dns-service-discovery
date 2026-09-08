from __future__ import annotations

import pytest

from beacon.cascadingfailure import (
    amplified_load,
    is_metastable,
    residual_load,
)
from beacon.errors import Invalid


class TestAmplifiedLoad:
    def test_under_capacity_is_not_amplified(self):
        assert amplified_load(offered=80, capacity=100, retry_multiplier=3) == 80

    def test_over_capacity_amplifies_by_the_retries(self):
        # 40 over capacity, each retried 3x -> 140 + 120 = 260... check
        assert amplified_load(140, capacity=100, retry_multiplier=3) == 140 + 120

    def test_a_negative_multiplier_is_refused(self):
        with pytest.raises(Invalid):
            amplified_load(100, 100, -1)


class TestMetastable:
    def test_a_spike_can_sustain_overload_after_it_passes(self):
        # base 80 under capacity 100, but a spike to 140 leaves
        # 40*3 = 120 residual retry load + 80 = 200 > 100
        assert residual_load(80, 140, 100, 3) == 200
        assert is_metastable(base=80, spike=140, capacity=100, retry_multiplier=3)

    def test_a_gentle_multiplier_recovers(self):
        # base 80, spike 140, 40 failures * 0.2 = 8 + 80 = 88 <= 100
        assert not is_metastable(80, 140, 100, retry_multiplier=0.2)

    def test_base_over_capacity_is_not_metastable_but_plain_overload(self):
        # if base itself exceeds capacity it is not the metastable case
        assert not is_metastable(120, 140, 100, retry_multiplier=3)
