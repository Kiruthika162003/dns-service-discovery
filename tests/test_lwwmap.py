from __future__ import annotations

from beacon.lwwmap import LWWMap


class TestSetGet:
    def test_a_set_value_is_read_back(self):
        m = LWWMap()
        m.set("k", "v1", timestamp=1, node="n1")
        assert m.get("k") == "v1"

    def test_a_later_write_wins(self):
        m = LWWMap()
        m.set("k", "v1", timestamp=1, node="n1")
        m.set("k", "v2", timestamp=2, node="n1")
        assert m.get("k") == "v2"

    def test_an_older_write_is_ignored(self):
        m = LWWMap()
        m.set("k", "v2", timestamp=5, node="n1")
        m.set("k", "v1", timestamp=2, node="n1")
        assert m.get("k") == "v2"


class TestMerge:
    def test_merge_takes_the_higher_stamp_per_key(self):
        a = LWWMap()
        a.set("k", "from-a", timestamp=1, node="a")
        b = LWWMap()
        b.set("k", "from-b", timestamp=2, node="b")
        assert a.merge(b).get("k") == "from-b"

    def test_merge_unions_distinct_keys(self):
        a = LWWMap()
        a.set("x", "1", 1, "a")
        b = LWWMap()
        b.set("y", "2", 1, "b")
        merged = a.merge(b)
        assert merged.get("x") == "1"
        assert merged.get("y") == "2"

    def test_merge_is_commutative(self):
        a = LWWMap()
        a.set("k", "from-a", 5, "a")
        b = LWWMap()
        b.set("k", "from-b", 5, "b")  # tie broken by node id
        assert a.merge(b).get("k") == b.merge(a).get("k")
