from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.mvcc import MVCC


class TestSnapshotRead:
    def test_a_read_sees_the_latest_committed_at_or_before_it(self):
        store = MVCC()
        store.write("k", "v1", commit_ts=10)
        store.write("k", "v2", commit_ts=20)
        assert store.read("k", snapshot_ts=15) == "v1"
        assert store.read("k", snapshot_ts=25) == "v2"

    def test_a_read_before_any_write_sees_nothing(self):
        store = MVCC()
        store.write("k", "v1", commit_ts=10)
        assert store.read("k", snapshot_ts=5) is None

    def test_a_reader_is_not_blocked_by_a_later_write(self):
        store = MVCC()
        store.write("k", "v1", commit_ts=10)
        # a snapshot at 10 keeps seeing v1 even after a write at 20
        store.write("k", "v2", commit_ts=20)
        assert store.read("k", snapshot_ts=10) == "v1"


class TestOrdering:
    def test_a_non_increasing_commit_is_refused(self):
        store = MVCC()
        store.write("k", "v1", commit_ts=20)
        with pytest.raises(Invalid):
            store.write("k", "v2", commit_ts=10)


class TestReclaim:
    def test_versions_below_the_oldest_snapshot_are_reclaimable(self):
        store = MVCC()
        store.write("k", "v1", commit_ts=10)
        store.write("k", "v2", commit_ts=20)
        store.write("k", "v3", commit_ts=30)
        # oldest live snapshot at 25: v1 is superseded by v2 (<=25)
        assert store.reclaimable("k", oldest_live_snapshot=25) == 1
