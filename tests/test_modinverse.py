from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.modinverse import extended_gcd, mod_inverse


class TestInverse:
    def test_the_inverse_undoes_the_multiplication(self):
        for a, m in [(3, 11), (7, 26), (17, 3120)]:
            inv = mod_inverse(a, m)
            assert (a * inv) % m == 1

    def test_a_known_inverse(self):
        assert mod_inverse(3, 11) == 4  # 3*4 = 12 = 1 mod 11

    def test_a_non_coprime_input_has_no_inverse(self):
        with pytest.raises(Invalid) as caught:
            mod_inverse(4, 8)
        assert "not coprime" in str(caught.value)

    def test_a_nonpositive_modulus_is_refused(self):
        with pytest.raises(Invalid):
            mod_inverse(3, 0)


class TestExtendedGcd:
    def test_it_returns_bezout_coefficients(self):
        g, x, y = extended_gcd(240, 46)
        assert g == 2
        assert 240 * x + 46 * y == g
