from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.primesieve import primes_up_to


class TestSieve:
    def test_primes_up_to_thirty(self):
        assert primes_up_to(30) == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]

    def test_the_bound_is_inclusive(self):
        assert 29 in primes_up_to(29)
        assert 30 not in primes_up_to(30)

    def test_below_two_there_are_no_primes(self):
        assert primes_up_to(1) == []
        assert primes_up_to(0) == []

    def test_the_count_of_primes_under_100(self):
        assert len(primes_up_to(100)) == 25


class TestRefusals:
    def test_a_negative_bound_is_refused(self):
        with pytest.raises(Invalid):
            primes_up_to(-1)
