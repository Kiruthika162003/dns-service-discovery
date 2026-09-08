from __future__ import annotations

import pytest

from beacon.chainreplication import Chain
from beacon.errors import Invalid


class TestRouting:
    def test_writes_traverse_head_to_tail(self):
        chain = Chain(["a", "b", "c"])
        assert chain.write_path() == ["a", "b", "c"]

    def test_reads_come_from_the_tail(self):
        chain = Chain(["a", "b", "c"])
        assert chain.read_node() == "c"

    def test_a_write_commits_at_the_tail(self):
        chain = Chain(["a", "b", "c"])
        assert not chain.committed("b")
        assert chain.committed("c")


class TestRecovery:
    def test_a_middle_node_is_spliced_out(self):
        chain = Chain(["a", "b", "c"])
        chain.remove("b")
        assert chain.write_path() == ["a", "c"]

    def test_removing_the_head_promotes_the_next(self):
        chain = Chain(["a", "b", "c"])
        chain.remove("a")
        assert chain.head() == "b"

    def test_removing_the_only_node_is_refused(self):
        with pytest.raises(Invalid):
            Chain(["a"]).remove("a")


class TestLatency:
    def test_a_longer_chain_costs_more_write_latency(self):
        assert Chain(["a", "b", "c"]).write_latency(per_hop=5) == 15
