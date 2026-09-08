from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.indirectprobe import (
    false_positive_rate,
    fanout_for_target,
    verdict,
)


class TestVerdict:
    def test_a_direct_ack_is_alive(self):
        assert verdict(True, []) == "alive-direct"

    def test_an_indirect_ack_rescues_a_bad_direct_path(self):
        assert verdict(False, [False, True, False]) == "alive-indirect"

    def test_all_paths_failing_is_a_suspect(self):
        assert verdict(False, [False, False, False]) == "suspect"


class TestCompoundedError:
    def test_more_paths_multiply_the_confidence(self):
        # 0.1 direct alone; with 2 indirect it is 0.1^3
        assert false_positive_rate(0.1, 0) == pytest.approx(0.1)
        assert false_positive_rate(0.1, 2) == pytest.approx(0.001)

    def test_a_drop_rate_outside_zero_to_one_is_refused(self):
        with pytest.raises(Invalid):
            false_positive_rate(1.5, 2)


class TestSizing:
    def test_fanout_grows_to_hit_a_target_rate(self):
        # 0.1 per link, want under 0.005: 0.1^2=0.01 too high,
        # 0.1^3=0.001 clears it, so fanout 2
        assert fanout_for_target(0.1, 0.005) == 2

    def test_a_certain_link_cannot_be_improved(self):
        with pytest.raises(Invalid):
            fanout_for_target(1.0, 0.001)
