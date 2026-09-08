from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.extendedrcode import compose, express, requires_opt, split


class TestCompose:
    def test_badvers_is_sixteen(self):
        # BADVERS = 16 = high 1, low 0
        assert compose(low4=0, high8=1) == 16

    def test_a_low_half_over_four_bits_is_refused(self):
        with pytest.raises(Invalid):
            compose(low4=16, high8=0)


class TestSplit:
    def test_split_recovers_the_halves(self):
        assert split(23) == (23 & 0xF, 23 >> 4)

    def test_a_plain_code_has_no_high_bits(self):
        assert split(3) == (3, 0)


class TestOptDependency:
    def test_a_plain_code_needs_no_opt(self):
        assert not requires_opt(3)
        assert express(3, has_opt=False) == 3

    def test_an_extended_code_needs_opt(self):
        assert requires_opt(16)
        assert express(16, has_opt=True) == 16

    def test_an_extended_code_without_opt_is_refused(self):
        with pytest.raises(Invalid) as caught:
            express(16, has_opt=False)
        assert "degrade to a plain code" in str(caught.value)
