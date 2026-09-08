from __future__ import annotations

import pytest

from beacon.cfsvruntime import CFS
from beacon.errors import Invalid


class TestPick:
    def test_the_lowest_vruntime_runs(self):
        cfs = CFS()
        cfs.add("a", 1024)
        cfs.add("b", 1024)
        cfs.run("a", actual=10)
        # a advanced, so b (still 0) is picked next
        assert cfs.pick() == "b"

    def test_no_task_is_refused(self):
        with pytest.raises(Invalid):
            CFS().pick()


class TestWeighting:
    def test_a_heavier_task_advances_its_clock_slower(self):
        cfs = CFS()
        cfs.add("light", 512)
        cfs.add("heavy", 2048)
        cfs.run("light", actual=10)
        cfs.run("heavy", actual=10)
        # same real time, but heavy's vruntime grew less
        assert cfs.vruntime["heavy"] < cfs.vruntime["light"]


class TestNewTask:
    def test_a_new_task_joins_at_the_current_minimum(self):
        cfs = CFS()
        cfs.add("a", 1024)
        cfs.run("a", actual=100)  # a's vruntime climbs
        cfs.add("b", 1024)
        # b joins at a's level, not a stale zero that would monopolize
        assert cfs.vruntime["b"] == cfs.vruntime["a"]

    def test_a_nonpositive_weight_is_refused(self):
        with pytest.raises(Invalid):
            CFS().add("a", 0)
