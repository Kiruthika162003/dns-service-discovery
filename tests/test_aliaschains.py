from __future__ import annotations

import pytest

from beacon.aliaschains import (
    chain_report,
    flatten_suggestion,
    follow_chain,
)
from beacon.errors import Invalid, Loop, Missing

CNAMES = {
    "vanity.example.": "lb.example.",
    "lb.example.": "endpoint.cloud.net.",
    "endpoint.cloud.net.": "region.cloud.net.",
}
ADDRESSES = {"region.cloud.net.": "203.0.113.50"}


class TestFollowing:
    def test_the_chain_walks_to_its_terminal(self):
        result = follow_chain(
            "vanity.example.", CNAMES, ADDRESSES
        )
        assert result.terminal == "203.0.113.50"
        assert len(result.hops) == 3
        assert result.cold_latency == 100

    def test_the_loop_is_caught_not_followed(self):
        looping = {
            "a.": "b.",
            "b.": "c.",
            "c.": "a.",
        }
        with pytest.raises(Loop) as caught:
            follow_chain("a.", looping, {})
        assert "caught, not followed forever" in str(
            caught.value
        )

    def test_the_dangling_end_is_a_delayed_outage(self):
        dangling = {"a.": "b.", "b.": "gone."}
        with pytest.raises(Missing) as caught:
            follow_chain("a.", dangling, {})
        assert "delayed anyone from noticing" in str(
            caught.value
        )


class TestTheReport:
    def test_the_long_chain_is_flagged(self):
        report = chain_report(
            "vanity.example.", CNAMES, ADDRESSES
        )
        assert "in 3 hop(s); cold latency 100 tick(s)" in report
        assert "no single team sees the whole chain" in report

    def test_a_short_chain_carries_no_lecture(self):
        short = {"a.": "b."}
        report = chain_report("a.", short, {"b.": "10.0.0.1"})
        assert "no single team" not in report


class TestFlattening:
    def test_the_suggestion_collapses_and_prices_it(self):
        suggestion = flatten_suggestion(
            "vanity.example.", CNAMES, ADDRESSES
        )
        assert "straight at 203.0.113.50" in suggestion
        assert "collapses 3 hop(s) and saves 75" in suggestion
        assert "the indirection each hop was bought to buy" in (
            suggestion
        )

    def test_a_one_hop_alias_is_already_short(self):
        short = {"a.": "b."}
        with pytest.raises(Invalid):
            flatten_suggestion("a.", short, {"b.": "10.0.0.1"})
