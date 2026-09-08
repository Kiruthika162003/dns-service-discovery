from __future__ import annotations

import pytest

from beacon.capacityplanner import (
    headroom,
    max_tolerable_failures,
    survives_failures,
)
from beacon.errors import Invalid


class TestSurvival:
    def test_a_cluster_with_margin_survives_a_failure(self):
        # 5 nodes, 100 each, load 350: after 1 fails, 4*100=400 >= 350
        assert survives_failures(5, 100, 350, k=1)

    def test_too_many_failures_overload_the_survivors(self):
        # after 2 fail, 3*100=300 < 350
        assert not survives_failures(5, 100, 350, k=2)

    def test_a_zero_capacity_is_refused(self):
        with pytest.raises(Invalid):
            survives_failures(5, 0, 100, k=1)


class TestMaxFailures:
    def test_it_finds_the_tolerance(self):
        # 5 nodes, 100 each, load 350 -> tolerates 1
        assert max_tolerable_failures(5, 100, 350) == 1

    def test_ample_capacity_tolerates_more(self):
        # load 150 -> after 3 fail, 2*100=200 >= 150 -> tolerates 3
        assert max_tolerable_failures(5, 100, 150) == 3


class TestHeadroom:
    def test_headroom_after_k_failures(self):
        assert headroom(5, 100, 350, k=1) == 50

    def test_negative_headroom_signals_overload(self):
        assert headroom(5, 100, 350, k=2) == -50
