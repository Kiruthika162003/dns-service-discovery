from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.exponentialdecay import DecayingCounter


class TestDecay:
    def test_a_fresh_add_reads_its_weight(self):
        counter = DecayingCounter(half_life=10)
        counter.add(now=0, amount=8)
        assert counter.get(now=0) == pytest.approx(8)

    def test_the_value_halves_over_a_half_life(self):
        counter = DecayingCounter(half_life=10)
        counter.add(now=0, amount=8)
        assert counter.get(now=10) == pytest.approx(4)
        assert counter.get(now=20) == pytest.approx(2)

    def test_a_spike_fades_toward_nothing(self):
        counter = DecayingCounter(half_life=10)
        counter.add(now=0, amount=100)
        assert counter.get(now=100) < 1


class TestAccumulation:
    def test_recent_adds_weigh_more_than_old(self):
        counter = DecayingCounter(half_life=10)
        counter.add(now=0, amount=1)  # decays to ~0.06 by now=40
        counter.add(now=40, amount=1)  # full weight
        value = counter.get(now=40)
        assert 1.0 < value < 1.1


class TestConstruction:
    def test_a_nonpositive_half_life_is_refused(self):
        with pytest.raises(Invalid):
            DecayingCounter(0)

    def test_time_running_backward_is_refused(self):
        counter = DecayingCounter(10)
        counter.add(now=10)
        with pytest.raises(Invalid):
            counter.get(now=5)
