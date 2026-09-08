from __future__ import annotations

from beacon.hybridclock import HybridClock


class TestLocal:
    def test_a_forward_physical_tick_resets_the_logical(self):
        clock = HybridClock("a")
        assert clock.local(10) == (10, 0)
        assert clock.local(20) == (20, 0)

    def test_a_stalled_physical_clock_bumps_the_logical(self):
        clock = HybridClock("a")
        clock.local(10)
        assert clock.local(10) == (10, 1)
        assert clock.local(10) == (10, 2)


class TestReceive:
    def test_a_future_message_pulls_the_clock_forward(self):
        clock = HybridClock("a")
        clock.local(10)
        wall, logical = clock.receive(10, msg_wall=25, msg_logical=3)
        assert wall == 25
        assert logical == 4

    def test_the_receive_stamp_exceeds_the_send_stamp(self):
        sender = HybridClock("a")
        receiver = HybridClock("b")
        s_wall, s_logical = sender.local(15)
        r_wall, r_logical = receiver.receive(12, s_wall, s_logical)
        assert (r_wall, r_logical) > (s_wall, s_logical)


class TestBoundedDrift:
    def test_the_clock_tracks_physical_time(self):
        clock = HybridClock("a")
        clock.local(100)
        assert clock.drift_from_physical(100) == 0

    def test_a_stalled_logical_run_does_not_outrun_the_wall(self):
        clock = HybridClock("a")
        clock.local(100)
        for _ in range(5):
            clock.local(100)
        # wall stays 100 no matter how many logical ticks
        assert clock.drift_from_physical(100) == 0
