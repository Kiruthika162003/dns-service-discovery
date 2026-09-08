from __future__ import annotations

from math import ceil

import pytest

from beacon.errors import Invalid
from beacon.shardrebalance import rebalance


class TestRebalance:
    def test_adding_a_node_moves_only_the_overflow(self):
        # 6 shards on 2 nodes, add a third
        assignment = {f"s{i}": ("a" if i < 3 else "b") for i in range(6)}
        result, moves = rebalance(assignment, ["a", "b", "c"])
        # target ceil(6/3)=2; a and b each shed 1 to c -> 2 moves
        assert moves == 2
        counts = dict.fromkeys(("a", "b", "c"), 0)
        for node in result.values():
            counts[node] += 1
        assert max(counts.values()) <= 2

    def test_a_removed_node_orphans_its_shards(self):
        assignment = {"s0": "a", "s1": "a", "s2": "gone"}
        result, moves = rebalance(assignment, ["a", "b"])
        # s2's node is gone, so it must move; a is at target 2 already
        assert result["s2"] in ("a", "b")
        assert moves >= 1

    def test_no_change_moves_nothing(self):
        assignment = {"s0": "a", "s1": "b"}
        result, moves = rebalance(assignment, ["a", "b"])
        assert moves == 0
        assert result == assignment


class TestBounds:
    def test_no_node_exceeds_the_target(self):
        assignment = {f"s{i}": "a" for i in range(10)}
        result, _ = rebalance(assignment, ["a", "b", "c"])
        target = ceil(10 / 3)
        counts = dict.fromkeys(("a", "b", "c"), 0)
        for node in result.values():
            counts[node] += 1
        assert max(counts.values()) <= target

    def test_no_nodes_is_refused(self):
        with pytest.raises(Invalid):
            rebalance({"s0": "a"}, [])
