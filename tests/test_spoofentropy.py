from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.spoofentropy import (
    attempts_for_even_chance,
    compare,
    entropy_bits,
)


class TestBits:
    def test_txid_alone_is_sixteen_bits(self):
        assert entropy_bits(txid=True, source_port_bits=0) == 16

    def test_the_sources_add(self):
        assert (
            entropy_bits(
                txid=True,
                source_port_bits=11,
                zero_x_twenty_letters=7,
            )
            == 16 + 11 + 7
        )

    def test_no_random_field_is_refused(self):
        with pytest.raises(Invalid) as caught:
            entropy_bits(
                txid=False,
                source_port_bits=0,
                zero_x_twenty_letters=0,
            )
        assert "matches on the first try" in str(caught.value)

    def test_negative_bits_are_refused(self):
        with pytest.raises(Invalid):
            entropy_bits(source_port_bits=-1)


class TestAttempts:
    def test_sixteen_bits_falls_in_tens_of_thousands(self):
        assert attempts_for_even_chance(16) == 2**15

    def test_stacked_entropy_is_astronomically_harder(self):
        assert attempts_for_even_chance(34) == 2**33

    def test_fewer_than_one_bit_is_refused(self):
        with pytest.raises(Invalid):
            attempts_for_even_chance(0)


class TestCompare:
    def test_the_comparison_names_the_gulf(self):
        line = compare(7)
        assert "txid alone: 32768 attempts" in line
        assert "practically unforgeable" in line
