from __future__ import annotations

from beacon.readyourwrites import acceptable, record_write


class TestAcceptable:
    def test_a_replica_with_the_write_may_serve(self):
        assert acceptable(last_write_version=7, replica_version=7)
        assert acceptable(last_write_version=7, replica_version=10)

    def test_a_replica_missing_the_write_may_not(self):
        assert not acceptable(last_write_version=7, replica_version=6)


class TestRecordWrite:
    def test_a_newer_write_advances_the_marker(self):
        assert record_write(last_write_version=3, new_write_version=8) == 8

    def test_the_client_never_reads_before_its_own_write(self):
        last = record_write(0, 5)
        # a replica at 4 cannot serve; the client would miss its write
        assert not acceptable(last, 4)
        assert acceptable(last, 5)
