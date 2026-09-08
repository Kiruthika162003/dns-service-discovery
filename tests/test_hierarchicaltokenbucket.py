from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.hierarchicaltokenbucket import HierarchicalTokenBucket


class TestConstruction:
    def test_a_nonpositive_ceiling_is_refused(self):
        with pytest.raises(Invalid):
            HierarchicalTokenBucket(0, {"a": 1})

    def test_no_children_is_refused(self):
        with pytest.raises(Invalid):
            HierarchicalTokenBucket(10, {})


class TestChildLimit:
    def test_a_child_is_held_to_its_own_rate(self):
        htb = HierarchicalTokenBucket(ceiling_rate=100, child_rates={"a": 2})
        assert htb.admit("a") == "admitted"
        assert htb.admit("a") == "admitted"
        assert htb.admit("a") == "denied-by-child"


class TestCeiling:
    def test_the_parent_ceiling_denies_when_drained(self):
        htb = HierarchicalTokenBucket(
            ceiling_rate=1, child_rates={"a": 5, "b": 5}
        )
        assert htb.admit("a") == "admitted"  # spends the one parent token
        assert htb.admit("b") == "denied-by-ceiling"


class TestRefill:
    def test_refill_restores_tokens_by_elapsed_time(self):
        htb = HierarchicalTokenBucket(ceiling_rate=10, child_rates={"a": 2})
        htb.admit("a")
        htb.admit("a")
        assert htb.admit("a") == "denied-by-child"
        htb.refill(elapsed=1.0)  # +2 child tokens, capped at 2
        assert htb.admit("a") == "admitted"

    def test_an_unknown_child_is_refused(self):
        htb = HierarchicalTokenBucket(10, {"a": 2})
        with pytest.raises(Invalid):
            htb.admit("ghost")
