from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.millerrabin import is_prime
from beacon.primesieve import primes_up_to


class TestPrimality:
    def test_it_agrees_with_the_sieve(self):
        sieve = set(primes_up_to(1000))
        for n in range(2, 1001):
            assert is_prime(n) == (n in sieve)

    def test_a_large_prime(self):
        assert is_prime(1_000_003)

    def test_a_mersenne_prime(self):
        assert is_prime(2**61 - 1)


class TestPseudoprimes:
    def test_a_carmichael_number_is_caught(self):
        # 561 fools Fermat's test but not Miller-Rabin
        assert not is_prime(561)

    def test_a_large_composite(self):
        assert not is_prime(1_000_004)


class TestRefusals:
    def test_below_two_is_refused(self):
        with pytest.raises(Invalid):
            is_prime(1)
