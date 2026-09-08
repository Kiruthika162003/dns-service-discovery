from __future__ import annotations

import pytest

from beacon.bandwidthdelay import bdp_bytes, fills_pipe, needs_window_scaling
from beacon.errors import Invalid


class TestBdp:
    def test_it_is_bandwidth_times_rtt_over_eight(self):
        # 100 Mbps over 100ms -> 100e6 * 0.1 / 8 = 1.25e6 bytes
        assert bdp_bytes(100_000_000, 0.1) == 1_250_000

    def test_a_negative_input_is_refused(self):
        with pytest.raises(Invalid):
            bdp_bytes(-1, 0.1)


class TestFillsPipe:
    def test_a_window_at_least_the_bdp_fills_it(self):
        assert fills_pipe(1_250_000, 100_000_000, 0.1)

    def test_a_smaller_window_throttles(self):
        assert not fills_pipe(65535, 100_000_000, 0.1)


class TestScaling:
    def test_a_fat_long_pipe_needs_scaling(self):
        assert needs_window_scaling(100_000_000, 0.1)

    def test_a_small_pipe_does_not(self):
        # 1 Mbps over 10ms -> 1250 bytes, well under 64KB
        assert not needs_window_scaling(1_000_000, 0.01)
