from __future__ import annotations

from beacon.lwwregister import LWWRegister


class TestMerge:
    def test_the_later_write_wins(self):
        a = LWWRegister("old", 1, "n1")
        b = LWWRegister("new", 2, "n2")
        assert a.merge(b).value == "new"

    def test_the_merge_is_commutative(self):
        a = LWWRegister("old", 1, "n1")
        b = LWWRegister("new", 2, "n2")
        assert a.merge(b) == b.merge(a)

    def test_the_merge_is_idempotent(self):
        a = LWWRegister("x", 3, "n1")
        assert a.merge(a) == a


class TestTieBreak:
    def test_the_node_id_breaks_a_timestamp_tie(self):
        low = LWWRegister("from-low", 5, "n1")
        high = LWWRegister("from-high", 5, "n2")
        assert low.merge(high).value == "from-high"
        assert high.merge(low).value == "from-high"


class TestAssign:
    def test_a_newer_assign_takes_effect(self):
        reg = LWWRegister("a", 1, "n1")
        assert reg.assign("b", 2, "n1").value == "b"

    def test_an_older_assign_is_ignored(self):
        reg = LWWRegister("a", 5, "n1")
        assert reg.assign("b", 2, "n1").value == "a"
