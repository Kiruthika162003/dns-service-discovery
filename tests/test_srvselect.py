from __future__ import annotations

import pytest

from beacon.errors import Invalid, Refused
from beacon.srvselect import SrvRecord, failover_order, select


def two_tier() -> list[SrvRecord]:
    return [
        SrvRecord(10, 1, "a.example.", 5060),
        SrvRecord(10, 3, "b.example.", 5060),
        SrvRecord(20, 5, "backup.example.", 5060),
    ]


class TestPriorityIsFailover:
    def test_the_backup_tier_is_never_chosen_first(self):
        for draw in range(20):
            chosen = select(two_tier(), draw)
            assert chosen.priority == 10

    def test_a_higher_weight_backup_still_loses_to_the_primary(
        self,
    ):
        chosen = select(two_tier(), 0)
        assert chosen.target != "backup.example."

    def test_failover_order_lists_priorities_ascending(self):
        assert failover_order(two_tier()) == [10, 20]


class TestWeightIsProportion:
    def test_the_split_follows_the_weights(self):
        picks = [select(two_tier(), draw).target for draw in range(4)]
        assert picks.count("a.example.") == 1
        assert picks.count("b.example.") == 3

    def test_all_zero_weights_split_by_index(self):
        group = [
            SrvRecord(5, 0, "x.example.", 1),
            SrvRecord(5, 0, "y.example.", 1),
        ]
        assert select(group, 0).target == "x.example."
        assert select(group, 1).target == "y.example."


class TestRefusals:
    def test_an_empty_set_is_refused(self):
        with pytest.raises(Invalid):
            select([], 0)

    def test_all_dot_targets_mean_service_not_offered(self):
        with pytest.raises(Refused) as caught:
            select([SrvRecord(0, 0, ".", 0)], 0)
        assert "not offered here" in str(caught.value)

    def test_a_negative_weight_is_refused(self):
        with pytest.raises(Invalid):
            SrvRecord(1, -1, "a.example.", 5060)
