from __future__ import annotations

import pytest

from beacon.entropy import (
    defense_table,
    forgeries_for_even_odds,
    guessing_space_bits,
)
from beacon.errors import Invalid

NAME = "www.example.com"


class TestTheSpace:
    def test_txid_alone_is_sixteen_bits(self):
        assert guessing_space_bits(NAME, False, False) == 16

    def test_ports_add_fourteen(self):
        assert guessing_space_bits(NAME, True, False) == 30

    def test_case_flipping_adds_a_bit_per_letter(self):
        assert guessing_space_bits(NAME, True, True) == 43


class TestTheOdds:
    def test_txid_alone_falls_in_seconds(self):
        assert forgeries_for_even_odds(
            NAME, False, False
        ) == 32_768

    def test_the_full_stack_is_not_winnable_in_a_window(self):
        needed = forgeries_for_even_odds(NAME, True, True)
        assert needed == 2**42

    def test_in_flight_duplicates_divide_the_defense(self):
        alone = forgeries_for_even_odds(NAME, True, False)
        flooded = forgeries_for_even_odds(
            NAME, True, False, in_flight=200
        )
        assert flooded == alone // 200

    def test_nothing_in_flight_is_nothing_to_poison(self):
        with pytest.raises(Invalid):
            forgeries_for_even_odds(
                NAME, True, True, in_flight=0
            )


class TestTheTable:
    def test_the_table_prices_each_stack(self):
        table = defense_table(NAME)
        assert "txid alone: 16 bit(s), 32768 forgeries" in table
        assert "txid + port: 30 bit(s)" in table
        assert "txid + port + 0x20: 43 bit(s)" in table
        assert "efficiency costume" in table
