from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.p2c import (
    assign_blind,
    assign_degenerate,
    assign_two_choice,
    comparison_table,
)


class TestTheMeasuredPromise:
    def test_blind_choice_stacks_by_luck(self):
        table = assign_blind(1000, 10)
        assert table.maximum() == 114
        assert table.spread() == 28

    def test_one_extra_look_collapses_the_spread(self):
        table = assign_two_choice(1000, 10)
        assert table.maximum() == 101
        assert table.spread() == 3

    def test_the_queues_are_nearly_flat(self):
        queues = sorted(assign_two_choice(1000, 10).queues)
        assert queues[0] >= 98
        assert queues[-1] <= 101

    def test_the_benefit_is_the_comparison_not_the_hash(self):
        rigged = assign_degenerate(1000, 10)
        blind = assign_blind(1000, 10)
        assert rigged.queues == blind.queues


class TestTheTable:
    def test_the_table_reads_side_by_side(self):
        table = comparison_table(1000, 10)
        assert "blind: max 114, spread 28" in table
        assert "two-choice: max 101, spread 3" in table
        assert (
            "the benefit is the comparison, not the second hash"
        ) in table

    def test_the_comparison_needs_company_and_load(self):
        with pytest.raises(Invalid):
            assign_blind(0, 10)
        with pytest.raises(Invalid):
            assign_two_choice(100, 1)
