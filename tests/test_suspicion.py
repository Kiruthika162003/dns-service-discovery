from __future__ import annotations

import math

import pytest

from beacon.errors import Invalid
from beacon.suspicion import scales_with_cluster, suspicion_timeout


class TestScaling:
    def test_the_timeout_follows_log_of_the_size(self):
        expected = 5.0 * math.log10(1000 + 1) * 2.0
        assert suspicion_timeout(1000, 2.0) == pytest.approx(expected)

    def test_a_bigger_cluster_waits_longer(self):
        assert scales_with_cluster(10, 10000, probe_interval=1.0)

    def test_the_growth_is_sublinear(self):
        small = suspicion_timeout(10, 1.0)
        big = suspicion_timeout(10000, 1.0)
        # 1000x the members, nowhere near 1000x the timeout
        assert big < small * 10


class TestRefusals:
    def test_an_empty_cluster_is_refused(self):
        with pytest.raises(Invalid):
            suspicion_timeout(0, 1.0)

    def test_a_nonpositive_probe_interval_is_refused(self):
        with pytest.raises(Invalid):
            suspicion_timeout(100, 0)
