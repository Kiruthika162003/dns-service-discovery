from __future__ import annotations

import pytest

from beacon.apdex import buckets, classify, score
from beacon.errors import Invalid


class TestClassify:
    def test_within_the_target_is_satisfied(self):
        assert classify(50, target=100) == "satisfied"

    def test_within_four_times_is_tolerating(self):
        assert classify(300, target=100) == "tolerating"

    def test_beyond_four_times_is_frustrated(self):
        assert classify(500, target=100) == "frustrated"

    def test_a_nonpositive_target_is_refused(self):
        with pytest.raises(Invalid):
            classify(50, target=0)


class TestScore:
    def test_all_satisfied_scores_one(self):
        assert score([10, 20, 30], target=100) == 1.0

    def test_tolerating_counts_half(self):
        # 2 satisfied, 2 tolerating -> (2 + 1)/4 = 0.75
        assert score([10, 10, 300, 300], target=100) == 0.75

    def test_an_empty_sample_is_refused(self):
        with pytest.raises(Invalid):
            score([], target=100)


class TestBuckets:
    def test_the_buckets_count_each_class(self):
        counts = buckets([10, 300, 500], target=100)
        assert counts == {
            "satisfied": 1,
            "tolerating": 1,
            "frustrated": 1,
        }
