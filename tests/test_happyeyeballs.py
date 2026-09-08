from __future__ import annotations

import pytest

from beacon.errors import Invalid
from beacon.happyeyeballs import DualStack


class TestBrokenIpv6:
    def test_naive_pays_the_whole_timeout_then_falls_back(self):
        stack = DualStack(ipv6_connect_ms=None, ipv4_connect_ms=30)
        assert stack.naive_ms() == 2000 + 30

    def test_happy_skips_the_stall_and_pays_only_the_delay(self):
        stack = DualStack(ipv6_connect_ms=None, ipv4_connect_ms=30)
        assert stack.happy_ms() == 50 + 30

    def test_the_savings_are_the_whole_timeout_minus_the_delay(
        self,
    ):
        stack = DualStack(ipv6_connect_ms=None, ipv4_connect_ms=30)
        assert stack.savings_ms() == 2000 - 50


class TestHealthyIpv6:
    def test_a_fast_v6_wins_inside_the_delay_and_ties_naive(self):
        stack = DualStack(ipv6_connect_ms=20, ipv4_connect_ms=30)
        assert stack.happy_ms() == 20
        assert stack.naive_ms() == 20

    def test_a_fast_v6_never_opens_the_second_connection(self):
        stack = DualStack(ipv6_connect_ms=20, ipv4_connect_ms=30)
        assert not stack.opens_second_connection()

    def test_the_doubled_load_is_a_myth_on_healthy_hosts(self):
        stack = DualStack(ipv6_connect_ms=20, ipv4_connect_ms=30)
        assert stack.savings_ms() == 0


class TestSlowIpv6:
    def test_a_slow_v6_opens_the_second_connection(self):
        stack = DualStack(ipv6_connect_ms=400, ipv4_connect_ms=30)
        assert stack.opens_second_connection()

    def test_the_faster_delayed_v4_can_still_win(self):
        stack = DualStack(ipv6_connect_ms=400, ipv4_connect_ms=30)
        assert stack.happy_ms() == 50 + 30

    def test_happy_is_never_slower_than_naive(self):
        stack = DualStack(ipv6_connect_ms=400, ipv4_connect_ms=30)
        assert stack.happy_ms() <= stack.naive_ms()


class TestRefusals:
    def test_two_dead_families_are_not_a_race(self):
        with pytest.raises(Invalid) as caught:
            DualStack(ipv6_connect_ms=None, ipv4_connect_ms=None)
        assert "only a failure to report" in str(caught.value)

    def test_a_delay_longer_than_the_timeout_is_refused(self):
        with pytest.raises(Invalid) as caught:
            DualStack(
                ipv6_connect_ms=10,
                ipv4_connect_ms=10,
                timeout_ms=40,
                resolution_delay_ms=50,
            )
        assert "before the primary has already given up" in str(
            caught.value
        )

    def test_the_description_names_the_winner(self):
        stack = DualStack(ipv6_connect_ms=None, ipv4_connect_ms=30)
        line = stack.describe()
        assert "ipv4 connects first" in line
        assert "second attempt opened" in line
