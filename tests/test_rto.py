from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.rto import RtoEstimator


class TestEstimate:
    def test_the_first_sample_seeds_the_estimate(self):
        est = RtoEstimator()
        est.sample(100)
        assert est.srtt == 100
        # rto = srtt + 4*rttvar = 100 + 4*50 = 300
        assert est.rto(minimum=1) == 300

    def test_a_steady_path_tightens_the_timeout(self):
        est = RtoEstimator()
        for _ in range(20):
            est.sample(100)
        # variance decays toward zero, so rto approaches srtt
        assert est.rto(minimum=1) < 200

    def test_the_floor_is_respected(self):
        est = RtoEstimator()
        est.sample(1)
        assert est.rto(minimum=50) == 50


class TestKarn:
    def test_a_retransmitted_sample_is_refused(self):
        est = RtoEstimator()
        with pytest.raises(Invalid) as caught:
            est.sample(100, retransmitted=True)
        assert "Karn's algorithm" in str(caught.value)

    def test_no_sample_yet_has_no_timeout(self):
        with pytest.raises(Invalid):
            RtoEstimator().rto()
