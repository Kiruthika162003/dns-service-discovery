from __future__ import annotations

import pytest

from beacon.deficitroundrobin import DeficitRoundRobin
from beacon.errors import Invalid


class TestConstruction:
    def test_a_zero_quantum_is_refused(self):
        with pytest.raises(Invalid):
            DeficitRoundRobin(quantum=0)


class TestScheduling:
    def test_small_packets_flow_within_the_quantum(self):
        drr = DeficitRoundRobin(quantum=100)
        queues = {"tiny": [10, 10, 10, 10, 10]}
        sent = drr.run_round(queues)
        assert drr.bytes_sent(sent)["tiny"] == 50

    def test_a_big_packet_waits_for_deficit_to_accumulate(self):
        drr = DeficitRoundRobin(quantum=100)
        queues = {"jumbo": [250]}
        assert drr.run_round(queues)["jumbo"] == []  # round 1
        assert drr.run_round(queues)["jumbo"] == []  # round 2
        assert drr.run_round(queues)["jumbo"] == [250]  # round 3

    def test_byte_fairness_over_rounds(self):
        drr = DeficitRoundRobin(quantum=100)
        queues = {"tiny": [40, 40, 40], "jumbo": [250]}
        total = {"tiny": 0, "jumbo": 0}
        for _ in range(4):
            sent = drr.run_round(queues)
            for queue, count in drr.bytes_sent(sent).items():
                total[queue] += count
        # both eventually drain, in byte proportion to their quanta
        assert total["tiny"] == 120
        assert total["jumbo"] == 250
