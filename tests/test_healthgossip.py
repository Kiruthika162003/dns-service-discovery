from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.healthgossip import DisseminationModel, scaling_table


class TestTheStar:
    def test_the_star_load_is_linear_in_the_fleet(self):
        assert DisseminationModel(fleet=1000).star_messages() == 999
        assert (
            DisseminationModel(fleet=1000).star_bottleneck_load()
            == 999
        )

    def test_a_fleet_of_one_cannot_disseminate(self):
        with pytest.raises(Invalid):
            DisseminationModel(fleet=1)


class TestTheEpidemic:
    def test_rounds_grow_logarithmically(self):
        assert DisseminationModel(fleet=10).epidemic_rounds() == 2
        assert DisseminationModel(fleet=100).epidemic_rounds() == 4
        assert DisseminationModel(fleet=1000).epidemic_rounds() == 5

    def test_gossip_sends_more_messages_not_fewer(self):
        model = DisseminationModel(fleet=1000)
        assert model.epidemic_messages() == 15000
        assert model.epidemic_messages() > model.star_messages()

    def test_a_zero_fanout_spreads_nothing(self):
        with pytest.raises(Invalid):
            DisseminationModel(fleet=10, fanout=0)


class TestTheReports:
    def test_the_tradeoff_names_the_real_win(self):
        report = DisseminationModel(fleet=1000).tradeoff_report()
        assert "more traffic, not less" in report
        assert "wins on the absent bottleneck, not on message count" in (
            report
        )

    def test_the_scaling_table_shows_the_gap(self):
        table = scaling_table([10, 100, 1000])
        assert "1000: bottleneck 999, gossip rounds 5" in table
        assert "that gap is the whole argument" in table

    def test_an_empty_table_is_refused(self):
        with pytest.raises(Invalid):
            scaling_table([])
