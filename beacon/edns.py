"""EDNS negotiation: agree on a bigger envelope, and fall back when it tears.

The 512-byte answer limit predates modern networks, and EDNS
lets a resolver advertise a larger buffer it can receive, but
the advertisement is a hope, not a guarantee: middleboxes drop
large UDP packets silently, so a resolver that advertises 4096
and gets nothing back cannot tell an empty answer from a
swallowed one. The negotiation this module models is the
careful dance real resolvers dance: advertise large, and on
silence, do not conclude the name is dead, retry with a
smaller buffer and finally with the flag that forces TCP,
because the failure mode of the naive path, treating a dropped
big packet as NXDOMAIN, poisons the cache with a false
negative that outlives the middlebox's bad moment. The ledger
records how often each buffer size was the one that worked,
which is a map of the path's real MTU that no configuration
file admits to, discovered by the traffic instead of guessed.
A path too small for even the 512-byte floor is not refused,
it forces TCP, because a resolver that gave up on tiny paths
would go blind exactly where the network is most constrained.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid

BUFFER_LADDER = (4096, 1232, 512)


@dataclass
class EdnsNegotiator:
    worked_at: dict[int, int] = field(default_factory=dict)
    forced_tcp: int = 0
    false_negatives_avoided: int = 0

    def negotiate(self, path_mtu: int, name: str) -> str:
        if path_mtu < 1:
            raise Invalid(
                "a path with no capacity carries nothing to "
                "negotiate over"
            )
        for buffer in BUFFER_LADDER:
            if buffer <= path_mtu:
                self.worked_at[buffer] = (
                    self.worked_at.get(buffer, 0) + 1
                )
                if buffer < BUFFER_LADDER[0]:
                    self.false_negatives_avoided += 1
                    return (
                        f"{name}: {BUFFER_LADDER[0]} was "
                        f"swallowed, {buffer} got through; the "
                        "silence was a torn envelope, not a "
                        "dead name"
                    )
                return (
                    f"{name}: negotiated {buffer}-byte buffer "
                    "on the first try"
                )
        self.forced_tcp += 1
        return (
            f"{name}: every UDP buffer was swallowed, forcing "
            "TCP; the last resort, not the first, because a "
            "handshake per query is a tax"
        )

    def path_mtu_map(self) -> str:
        if not self.worked_at and not self.forced_tcp:
            raise Invalid("no negotiations to map")
        lines = ["the path's real MTU, discovered by traffic:"]
        for buffer in BUFFER_LADDER:
            count = self.worked_at.get(buffer, 0)
            if count:
                lines.append(f"  {buffer} bytes: {count} time(s)")
        if self.forced_tcp:
            lines.append(f"  forced TCP: {self.forced_tcp} time(s)")
        lines.append(
            f"{self.false_negatives_avoided} false negative(s) "
            "avoided by retrying instead of trusting the "
            "silence"
        )
        return "\n".join(lines)
