from __future__ import annotations

from beacon.deadlockdetection import find_cycle, has_deadlock


class TestNoDeadlock:
    def test_an_acyclic_graph_has_no_deadlock(self):
        wait_for = {"t1": {"t2"}, "t2": {"t3"}, "t3": set()}
        assert not has_deadlock(wait_for)
        assert find_cycle(wait_for) == []

    def test_an_empty_graph_is_healthy(self):
        assert not has_deadlock({})


class TestDeadlock:
    def test_a_two_cycle_is_a_deadlock(self):
        wait_for = {"t1": {"t2"}, "t2": {"t1"}}
        assert has_deadlock(wait_for)

    def test_the_cycle_is_returned_for_a_victim(self):
        wait_for = {"t1": {"t2"}, "t2": {"t3"}, "t3": {"t1"}}
        cycle = find_cycle(wait_for)
        assert set(cycle) == {"t1", "t2", "t3"}

    def test_a_cycle_among_a_larger_graph_is_found(self):
        wait_for = {
            "t1": {"t2"},
            "t2": {"t3"},
            "t3": {"t2"},  # t2 <-> t3 cycle
            "t4": set(),
        }
        assert has_deadlock(wait_for)
        assert set(find_cycle(wait_for)) == {"t2", "t3"}
