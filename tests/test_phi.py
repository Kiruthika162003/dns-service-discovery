from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.phi import PhiDetector


class TestConstruction:
    def test_a_nonpositive_mean_is_refused(self):
        with pytest.raises(Invalid):
            PhiDetector(mean_interval=0)


class TestPhiRises:
    def test_phi_is_zero_at_no_elapsed_time(self):
        assert PhiDetector(1.0).phi(0) == pytest.approx(0.0)

    def test_phi_climbs_with_silence(self):
        detector = PhiDetector(1.0)
        assert detector.phi(5) > detector.phi(2)

    def test_a_negative_elapsed_is_refused(self):
        with pytest.raises(Invalid):
            PhiDetector(1.0).phi(-1)


class TestRelativeLateness:
    def test_the_same_relative_lateness_gives_the_same_phi(self):
        fast = PhiDetector(1.0)
        slow = PhiDetector(10.0)
        assert fast.phi(3) == pytest.approx(slow.phi(30))


class TestThreshold:
    def test_suspicion_crosses_at_the_threshold(self):
        detector = PhiDetector(1.0)
        # phi(elapsed) = elapsed / (mean * ln 10); threshold 8 ->
        # elapsed ~ 8 * ln 10 ~ 18.4
        assert not detector.suspect(10, threshold=8.0)
        assert detector.suspect(20, threshold=8.0)
