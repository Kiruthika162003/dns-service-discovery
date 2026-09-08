from __future__ import annotations

import pytest

from beacon.errors import Refused
from beacon.logmatching import append


class TestAppend:
    def test_a_matching_predecessor_appends(self):
        log = [1, 1, 2]
        result = append(log, prev_index=3, prev_term=2, entries=[3])
        assert result == [1, 1, 2, 3]

    def test_an_append_at_the_empty_log_start_is_allowed(self):
        assert append([], prev_index=0, prev_term=0, entries=[1]) == [1]


class TestConvergence:
    def test_a_conflicting_suffix_is_truncated(self):
        # follower has a stale term-2 entry at index 3; leader
        # sends prev_index 2 (term 1) with the correct suffix
        log = [1, 1, 2]
        result = append(log, prev_index=2, prev_term=1, entries=[3, 3])
        assert result == [1, 1, 3, 3]

    def test_a_conflict_at_the_predecessor_is_refused(self):
        log = [1, 1, 2]
        with pytest.raises(Refused) as caught:
            append(log, prev_index=3, prev_term=1, entries=[4])
        assert "conflict to truncate" in str(caught.value)


class TestGaps:
    def test_a_gap_beyond_the_log_is_refused(self):
        log = [1, 1]
        with pytest.raises(Refused) as caught:
            append(log, prev_index=5, prev_term=1, entries=[2])
        assert "the follower is behind" in str(caught.value)
