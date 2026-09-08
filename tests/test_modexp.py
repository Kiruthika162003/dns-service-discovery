from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.modexp import mod_exp


class TestModExp:
    def test_it_matches_the_builtin(self):
        for base, exp, mod in [(2, 10, 1000), (3, 7, 13), (7, 0, 5), (5, 3, 1)]:
            assert mod_exp(base, exp, mod) == pow(base, exp, mod)

    def test_a_large_exponent_is_cheap_and_correct(self):
        # would be intractable naively; square-and-multiply handles it
        assert mod_exp(2, 1_000_000, 1_000_000_007) == pow(
            2, 1_000_000, 1_000_000_007
        )

    def test_exponent_zero_is_one(self):
        assert mod_exp(123, 0, 97) == 1


class TestRefusals:
    def test_a_nonpositive_modulus_is_refused(self):
        with pytest.raises(Invalid):
            mod_exp(2, 10, 0)

    def test_a_negative_exponent_is_refused(self):
        with pytest.raises(Invalid) as caught:
            mod_exp(2, -1, 7)
        assert "modular inverse" in str(caught.value)
