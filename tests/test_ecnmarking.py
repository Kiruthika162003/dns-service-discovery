from __future__ import annotations

import pytest

from beacon.ecnmarking import action
from beacon.errors import Invalid


class TestAction:
    def test_a_shallow_queue_forwards(self):
        assert action(5, mark_threshold=10, drop_threshold=20, ecn_capable=True) == (
            "forward"
        )

    def test_a_medium_queue_marks_an_ecn_flow(self):
        assert action(15, mark_threshold=10, drop_threshold=20, ecn_capable=True) == (
            "mark"
        )

    def test_a_medium_queue_drops_a_non_ecn_flow(self):
        assert action(15, mark_threshold=10, drop_threshold=20, ecn_capable=False) == (
            "drop"
        )

    def test_a_full_queue_drops_even_an_ecn_flow(self):
        assert action(25, mark_threshold=10, drop_threshold=20, ecn_capable=True) == (
            "drop"
        )


class TestThresholds:
    def test_mark_at_or_above_drop_is_refused(self):
        with pytest.raises(Invalid) as caught:
            action(5, mark_threshold=20, drop_threshold=20, ecn_capable=True)
        assert "ECN never" in str(caught.value)
