from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.tcpkeepalive import (
    handshakes_saved,
    handshakes_with_keepalive,
    handshakes_without_keepalive,
    idle_sockets_held,
)


class TestBaseline:
    def test_without_keepalive_every_query_handshakes(self):
        assert handshakes_without_keepalive(5) == 5

    def test_a_negative_workload_is_refused(self):
        with pytest.raises(Invalid):
            handshakes_without_keepalive(-1)


class TestReuse:
    def test_gaps_under_the_timeout_reuse_one_connection(self):
        # 4 gaps all under timeout -> 5 queries, 1 handshake
        assert handshakes_with_keepalive([10, 20, 30, 40], 100) == 1

    def test_a_gap_over_the_timeout_forces_a_new_handshake(self):
        assert handshakes_with_keepalive([10, 500, 20], 100) == 2

    def test_the_savings_are_the_handshakes_avoided(self):
        # 5 queries: baseline 5, keepalive 1, saved 4
        assert handshakes_saved([10, 20, 30, 40], 100) == 4

    def test_a_negative_timeout_is_refused(self):
        with pytest.raises(Invalid):
            handshakes_with_keepalive([10], -1)


class TestTheCost:
    def test_the_idle_socket_warning_names_the_exhaustion(self):
        line = idle_sockets_held(1000, 30000)
        assert "1000 idle socket(s)" in line
        assert "exhaust" in line
