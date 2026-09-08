from __future__ import annotations

from beacon.mvregister import MVRegister


class TestSingleWriter:
    def test_a_dominating_write_replaces(self):
        reg = MVRegister()
        reg.write("v1", {"a": 1})
        reg.write("v2", {"a": 2})  # a's later write dominates
        assert reg.read() == ["v2"]
        assert not reg.has_conflict()


class TestConcurrent:
    def test_concurrent_writes_are_both_kept(self):
        reg = MVRegister()
        reg.write("from-a", {"a": 1})
        reg.write("from-b", {"b": 1})  # concurrent with a's write
        assert reg.read() == ["from-a", "from-b"]
        assert reg.has_conflict()

    def test_a_merged_write_collapses_the_conflict(self):
        reg = MVRegister()
        reg.write("from-a", {"a": 1})
        reg.write("from-b", {"b": 1})
        # a resolving write that saw both dominates them
        reg.write("merged", {"a": 1, "b": 1, "c": 1})
        assert reg.read() == ["merged"]
        assert not reg.has_conflict()


class TestStaleWrite:
    def test_a_stale_write_is_not_added(self):
        reg = MVRegister()
        reg.write("current", {"a": 2})
        # a write that the current value already dominates
        reg.write("stale", {"a": 1})
        assert reg.read() == ["current"]
