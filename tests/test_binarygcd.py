from __future__ import annotations

import math

import pytest

from beacon.binarygcd import binary_gcd
from beacon.errors import Invalid


class TestBinaryGcd:
    def test_it_agrees_with_the_standard_library(self):
        for a in range(0, 60):
            for b in range(0, 60):
                assert binary_gcd(a, b) == math.gcd(a, b)

    def test_a_known_pair(self):
        assert binary_gcd(48, 36) == 12

    def test_gcd_with_zero_is_the_other_operand(self):
        assert binary_gcd(0, 7) == 7
        assert binary_gcd(7, 0) == 7

    def test_coprime_numbers_give_one(self):
        assert binary_gcd(17, 5) == 1

    def test_it_handles_large_powers_of_two(self):
        assert binary_gcd(2**40, 2**30) == 2**30


class TestRefusals:
    def test_a_negative_operand_is_refused(self):
        with pytest.raises(Invalid):
            binary_gcd(-4, 8)
