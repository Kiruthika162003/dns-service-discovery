from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.hyperperiod import gcd, hyperperiod, lcm


class TestGcd:
    def test_it_finds_the_greatest_common_divisor(self):
        assert gcd(12, 18) == 6
        assert gcd(17, 5) == 1

    def test_gcd_with_zero(self):
        assert gcd(7, 0) == 7


class TestLcm:
    def test_it_finds_the_least_common_multiple(self):
        assert lcm(4, 6) == 12
        assert lcm(3, 5) == 15

    def test_a_nonpositive_period_is_refused(self):
        with pytest.raises(Invalid):
            lcm(0, 5)


class TestHyperperiod:
    def test_harmonic_periods_stay_small(self):
        # 1,2,4,8 each divides the next -> hyperperiod 8
        assert hyperperiod([1, 2, 4, 8]) == 8

    def test_coprime_periods_explode(self):
        # 3,5,7 coprime -> product 105
        assert hyperperiod([3, 5, 7]) == 105

    def test_no_periods_is_refused(self):
        with pytest.raises(Invalid):
            hyperperiod([])
