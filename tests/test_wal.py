from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.wal import WriteAheadLog


class TestAppendAndReplay:
    def test_appended_records_are_the_replay_set_until_applied(self):
        wal = WriteAheadLog()
        wal.append("set a=1")
        wal.append("set b=2")
        assert wal.replay() == ["set a=1", "set b=2"]

    def test_applying_shrinks_the_replay_set(self):
        wal = WriteAheadLog()
        wal.append("set a=1")
        wal.append("set b=2")
        wal.apply_up_to(1)
        assert wal.replay() == ["set b=2"]


class TestRecovery:
    def test_a_crash_replays_the_unapplied_tail(self):
        wal = WriteAheadLog()
        wal.append("set a=1")
        wal.append("set b=2")
        wal.apply_up_to(1)  # a=1 persisted, b=2 not
        # after a crash, recovery replays what was logged but not applied
        assert wal.replay() == ["set b=2"]

    def test_the_applied_point_cannot_move_backward(self):
        wal = WriteAheadLog()
        wal.append("x")
        wal.append("y")
        wal.apply_up_to(2)
        with pytest.raises(Invalid):
            wal.apply_up_to(1)


class TestCheckpoint:
    def test_a_checkpoint_truncates_applied_records(self):
        wal = WriteAheadLog()
        wal.append("a")
        wal.append("b")
        wal.apply_up_to(2)
        wal.checkpoint()
        assert wal.replay() == []
        assert len(wal.records) == 0
