from __future__ import annotations

import pytest

from beacon.crt import solve
from beacon.errors import Invalid


class TestSolve:
    def test_the_classic_three_congruence_system(self):
        # x = 2 (mod 3), 3 (mod 5), 2 (mod 7) has the unique solution 23
        assert solve([2, 3, 2], [3, 5, 7]) == 23

    def test_the_solution_satisfies_every_congruence(self):
        remainders = [1, 2, 6]
        moduli = [2, 3, 7]
        x = solve(remainders, moduli)
        for r, m in zip(remainders, moduli, strict=True):
            assert x % m == r

    def test_a_single_congruence_returns_the_remainder(self):
        assert solve([4], [9]) == 4

    def test_the_result_is_reduced_modulo_the_product(self):
        x = solve([0, 0], [3, 5])
        assert 0 <= x < 15
        assert x == 0


class TestRefusals:
    def test_moduli_that_share_a_factor_are_refused(self):
        with pytest.raises(Invalid):
            solve([1, 2], [4, 6])  # gcd(4, 6) = 2

    def test_a_nonpositive_modulus_is_refused(self):
        with pytest.raises(Invalid):
            solve([1], [0])

    def test_mismatched_lengths_are_refused(self):
        with pytest.raises(Invalid):
            solve([1, 2], [3])

    def test_no_congruences_is_refused(self):
        with pytest.raises(Invalid):
            solve([], [])
