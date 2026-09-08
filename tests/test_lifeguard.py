from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.lifeguard import Lifeguard


class TestConstruction:
    def test_a_ceiling_below_one_is_refused(self):
        with pytest.raises(Invalid):
            Lifeguard(max_multiplier=0)


class TestTheMultiplier:
    def test_a_healthy_node_uses_the_base_timeout(self):
        guard = Lifeguard()
        assert guard.is_healthy()
        assert guard.scaled_timeout(100) == 100

    def test_missed_acks_stretch_the_timeout(self):
        guard = Lifeguard()
        guard.on_missed_ack()
        guard.on_missed_ack()
        assert guard.scaled_timeout(100) == 300

    def test_clean_probes_recover_the_health(self):
        guard = Lifeguard()
        guard.on_missed_ack()
        guard.on_missed_ack()
        guard.on_clean_probe()
        assert guard.scaled_timeout(100) == 200

    def test_the_multiplier_is_bounded_above(self):
        guard = Lifeguard(max_multiplier=3)
        for _ in range(10):
            guard.on_missed_ack()
        assert guard.scaled_timeout(100) == 400

    def test_health_never_goes_negative(self):
        guard = Lifeguard()
        for _ in range(5):
            guard.on_clean_probe()
        assert guard.is_healthy()
        assert guard.scaled_timeout(100) == 100
