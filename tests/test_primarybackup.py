from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.primarybackup import ack_latency, data_loss_window


class TestLatency:
    def test_synchronous_pays_the_backup_round_trip(self):
        assert ack_latency(primary_ms=5, backup_ms=8, synchronous=True) == 13

    def test_asynchronous_pays_only_the_primary(self):
        assert ack_latency(primary_ms=5, backup_ms=8, synchronous=False) == 5

    def test_a_negative_latency_is_refused(self):
        with pytest.raises(Invalid):
            ack_latency(-1, 8, synchronous=True)


class TestDataLoss:
    def test_synchronous_loses_nothing(self):
        assert data_loss_window(unreplicated_writes=40, synchronous=True) == 0

    def test_asynchronous_loses_the_unreplicated_window(self):
        assert data_loss_window(40, synchronous=False) == 40

    def test_a_negative_count_is_refused(self):
        with pytest.raises(Invalid):
            data_loss_window(-1, synchronous=False)
