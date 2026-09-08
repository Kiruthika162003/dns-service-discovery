from __future__ import annotations

import pytest

from beacon.dohpadding import PaddingAnalysis, pad_to_block
from beacon.errors import Invalid

SIZES = (43, 87, 91, 120, 200, 305)


def analysis() -> PaddingAnalysis:
    return PaddingAnalysis(message_sizes=SIZES)


class TestPadding:
    def test_rounding_goes_up_to_the_block(self):
        assert pad_to_block(43, 128) == 128
        assert pad_to_block(128, 128) == 128
        assert pad_to_block(129, 128) == 256

    def test_positive_sizes_and_blocks(self):
        with pytest.raises(Invalid):
            pad_to_block(0, 128)
        with pytest.raises(Invalid):
            pad_to_block(43, 0)


class TestTheTradeoff:
    def test_a_bigger_block_hides_more_lengths(self):
        chosen = analysis()
        assert chosen.observable_lengths(128) == 3
        assert chosen.observable_lengths(468) == 1

    def test_a_bigger_block_costs_more_bytes(self):
        chosen = analysis()
        assert chosen.padding_bytes(128) == 306
        assert chosen.padding_bytes(468) == 1962

    def test_the_privacy_report_names_the_dial(self):
        report = analysis().privacy_report(128)
        assert (
            "6 distinct length(s) collapse to 3, spending 306"
        ) in report
        assert "a dial not a checkbox" in report

    def test_an_empty_analysis_is_refused(self):
        with pytest.raises(Invalid):
            PaddingAnalysis(message_sizes=())


class TestTheComparison:
    def test_the_table_shows_privacy_against_bytes(self):
        table = analysis().compare_blocks([128, 468])
        assert "128: 3 length(s), 306 byte(s)" in table
        assert "468: 1 length(s), 1962 byte(s)" in table
        assert "measures the wrong axis" in table

    def test_an_empty_comparison_is_refused(self):
        with pytest.raises(Invalid):
            analysis().compare_blocks([])
