from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.snapshotinstall import catch_up_plan, should_snapshot


class TestThreshold:
    def test_a_log_over_the_threshold_snapshots(self):
        assert should_snapshot(log_size=1000, threshold=1000)
        assert not should_snapshot(log_size=999, threshold=1000)

    def test_a_threshold_below_one_is_refused(self):
        with pytest.raises(Invalid):
            should_snapshot(10, threshold=0)


class TestCatchUp:
    def test_a_follower_behind_the_snapshot_needs_an_install(self):
        # snapshot covers up to index 500; follower needs index 300
        assert catch_up_plan(300, snapshot_last_index=500) == (
            "install-snapshot"
        )

    def test_a_follower_ahead_of_the_snapshot_gets_appends(self):
        assert catch_up_plan(700, snapshot_last_index=500) == (
            "append-entries"
        )

    def test_a_follower_exactly_at_the_snapshot_needs_install(self):
        assert catch_up_plan(500, snapshot_last_index=500) == (
            "install-snapshot"
        )

    def test_a_next_index_below_one_is_refused(self):
        with pytest.raises(Invalid):
            catch_up_plan(0, snapshot_last_index=500)
