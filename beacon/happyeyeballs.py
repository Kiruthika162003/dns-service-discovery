"""Dual-stack racing: the fast address wins, and a dead family never stalls the connect.

A name resolves to both an IPv6 and an IPv4 address, and the
naive client tries IPv6 first and only falls back to IPv4 after
the IPv6 attempt times out, which means a host with broken IPv6
pays the entire connection timeout before the working address
is ever tried. Happy Eyeballs, RFC 8305, refuses that stall: it
starts the IPv6 attempt, waits only a short resolution delay,
and if IPv6 has not connected by then starts IPv4 in parallel,
taking whichever connects first. One expects the cost of this to
be a permanently doubled connection load, since it races two
families at once, and measurement refutes that: a healthy IPv6
host connects inside the resolution delay and the second attempt
is never started, so the doubled load appears only on the slow
hosts that actually need the hedge. The naive strategy is cheaper
by exactly one connection attempt precisely when IPv6 works, and
catastrophic by a full timeout precisely when it does not, which
is the trade the delay is tuned to win.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid


@dataclass(frozen=True)
class DualStack:
    ipv6_connect_ms: int | None
    ipv4_connect_ms: int | None
    timeout_ms: int = 2000
    resolution_delay_ms: int = 50

    def __post_init__(self) -> None:
        if (
            self.ipv6_connect_ms is None
            and self.ipv4_connect_ms is None
        ):
            raise Invalid(
                "both address families are unreachable; there "
                "is no connection to race, only a failure to "
                "report"
            )
        if self.resolution_delay_ms >= self.timeout_ms:
            raise Invalid(
                "the resolution delay must be shorter than the "
                "timeout, or the fallback family never starts "
                "before the primary has already given up"
            )

    def naive_ms(self) -> int:
        if self.ipv6_connect_ms is not None:
            return self.ipv6_connect_ms
        return self.timeout_ms + self.ipv4_connect_ms

    def _v6_beats_the_delay(self) -> bool:
        return (
            self.ipv6_connect_ms is not None
            and self.ipv6_connect_ms <= self.resolution_delay_ms
        )

    def happy_ms(self) -> int:
        if self._v6_beats_the_delay():
            return self.ipv6_connect_ms
        candidates = []
        if self.ipv6_connect_ms is not None:
            candidates.append(self.ipv6_connect_ms)
        if self.ipv4_connect_ms is not None:
            candidates.append(
                self.resolution_delay_ms + self.ipv4_connect_ms
            )
        return min(candidates)

    def opens_second_connection(self) -> bool:
        return not self._v6_beats_the_delay()

    def savings_ms(self) -> int:
        return self.naive_ms() - self.happy_ms()

    def describe(self) -> str:
        winner = "ipv6" if self._winner_is_v6() else "ipv4"
        return (
            f"naive {self.naive_ms()}ms vs happy "
            f"{self.happy_ms()}ms, {winner} connects first; "
            f"second attempt "
            f"{'opened' if self.opens_second_connection() else 'never started'}"
        )

    def _winner_is_v6(self) -> bool:
        if self._v6_beats_the_delay():
            return True
        v6 = self.ipv6_connect_ms
        if v6 is None:
            return False
        if self.ipv4_connect_ms is None:
            return True
        return v6 <= self.resolution_delay_ms + self.ipv4_connect_ms
