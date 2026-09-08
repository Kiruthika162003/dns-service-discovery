from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.tcpstates import lingers_in_time_wait, transition


class TestHandshake:
    def test_the_active_open_three_way(self):
        state = transition("CLOSED", "active-open")
        assert state == "SYN_SENT"
        assert transition(state, "recv-syn-ack") == "ESTABLISHED"

    def test_the_passive_open_three_way(self):
        assert transition("CLOSED", "passive-open") == "LISTEN"
        assert transition("LISTEN", "recv-syn") == "SYN_RECEIVED"
        assert transition("SYN_RECEIVED", "recv-ack") == "ESTABLISHED"


class TestClose:
    def test_the_active_close_reaches_time_wait(self):
        assert transition("ESTABLISHED", "close") == "FIN_WAIT_1"
        assert transition("FIN_WAIT_1", "recv-ack") == "FIN_WAIT_2"
        assert transition("FIN_WAIT_2", "recv-fin") == "TIME_WAIT"

    def test_time_wait_lingers_then_closes_on_timeout(self):
        assert lingers_in_time_wait("TIME_WAIT")
        assert transition("TIME_WAIT", "timeout") == "CLOSED"


class TestViolations:
    def test_an_undefined_transition_is_refused(self):
        with pytest.raises(Invalid) as caught:
            transition("ESTABLISHED", "recv-syn-ack")
        assert "protocol violation" in str(caught.value)
