from __future__ import annotations

from beacon.monotonicreads import acceptable, observe


class TestAcceptable:
    def test_a_caught_up_replica_may_serve(self):
        assert acceptable(session_watermark=5, replica_version=5)
        assert acceptable(session_watermark=5, replica_version=8)

    def test_a_lagging_replica_may_not(self):
        assert not acceptable(session_watermark=5, replica_version=3)


class TestObserve:
    def test_reading_a_newer_version_advances_the_watermark(self):
        assert observe(session_watermark=5, read_version=9) == 9

    def test_reading_an_older_version_does_not_regress_it(self):
        assert observe(session_watermark=5, read_version=2) == 5

    def test_the_timeline_never_moves_backward(self):
        watermark = 0
        for version in (3, 7, 4, 9, 8):
            if acceptable(watermark, version):
                watermark = observe(watermark, version)
        assert watermark == 9
