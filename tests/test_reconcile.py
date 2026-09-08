from __future__ import annotations

from beacon.reconcile import converged, reconcile


class TestReconcile:
    def test_it_computes_creates_deletes_and_updates(self):
        desired = {"a": "1", "b": "2", "c": "3"}
        actual = {"b": "9", "c": "3", "d": "4"}
        create, delete, update = reconcile(desired, actual)
        assert create == ["a"]
        assert delete == ["d"]
        assert update == ["b"]

    def test_an_aligned_state_is_converged(self):
        state = {"a": "1", "b": "2"}
        assert converged(state, dict(state))

    def test_a_drifted_state_is_not_converged(self):
        assert not converged({"a": "1"}, {"a": "2"})


class TestLevelTriggered:
    def test_a_missed_event_is_fixed_on_the_next_pass(self):
        desired = {"a": "1"}
        actual: dict[str, str] = {}  # a create event was lost
        # reconcile from state still sees a must be created
        create, _, _ = reconcile(desired, actual)
        assert create == ["a"]
