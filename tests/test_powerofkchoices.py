from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.powerofkchoices import KChoices

BACKENDS = [f"b{i}" for i in range(20)]
KEYS = [f"req-{i}" for i in range(4000)]


class TestConstruction:
    def test_a_k_over_the_backend_count_is_refused(self):
        with pytest.raises(Invalid):
            KChoices(BACKENDS, k=25)

    def test_no_backends_is_refused(self):
        with pytest.raises(Invalid):
            KChoices([], k=1)


class TestPlacement:
    def test_every_key_is_placed(self):
        balancer = KChoices(BACKENDS, k=2)
        balancer.place_all(KEYS)
        assert sum(balancer.load.values()) == len(KEYS)


class TestDiminishingReturns:
    def test_two_choices_beat_one(self):
        one = KChoices(BACKENDS, k=1)
        one.place_all(KEYS)
        two = KChoices(BACKENDS, k=2)
        two.place_all(KEYS)
        assert two.max_over_average() < one.max_over_average()

    def test_the_gain_from_two_to_three_is_smaller(self):
        one = KChoices(BACKENDS, k=1)
        one.place_all(KEYS)
        two = KChoices(BACKENDS, k=2)
        two.place_all(KEYS)
        three = KChoices(BACKENDS, k=3)
        three.place_all(KEYS)
        first_gain = one.max_over_average() - two.max_over_average()
        second_gain = two.max_over_average() - three.max_over_average()
        assert first_gain > second_gain
