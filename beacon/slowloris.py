"""Slow-drip connection defense: the attacker who ties up sockets by inches.

A TCP-based resolver has a finite pool of connection slots, and
the cheapest denial of service is not a flood but a trickle: an
attacker opens connections and sends one byte at a time, or
nothing, holding each slot open with almost no effort while
legitimate connections are turned away for lack of slots. The
defense is per-connection progress accounting: a connection
that has not made meaningful progress within a deadline is
reaped to free its slot, and the deadline is on progress, not
on total duration, because a legitimately slow but advancing
transfer is fine while a stalled one is the attack. The pool
also caps connections per source so one address cannot occupy
the whole pool, and the report separates slots reaped for
stalling from slots closed normally, because a spike of
stall-reaps is the signature of the attack and a defense that
cannot show that number is guessing about whether it is under
attack at all.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid

PROGRESS_DEADLINE = 10
PER_SOURCE_CAP = 3


@dataclass
class Connection:
    conn_id: str
    source: str
    opened_at: int
    last_progress_at: int
    bytes_seen: int = 0


@dataclass
class ConnectionPool:
    capacity: int
    active: dict[str, Connection] = field(default_factory=dict)
    stall_reaps: int = 0
    normal_closes: int = 0
    rejected_for_cap: int = 0

    def __post_init__(self) -> None:
        if self.capacity < 1:
            raise Invalid("a pool of zero slots serves nobody")

    def _by_source(self, source: str) -> int:
        return sum(
            1
            for conn in self.active.values()
            if conn.source == source
        )

    def open(
        self, conn_id: str, source: str, now: int
    ) -> str:
        if len(self.active) >= self.capacity:
            raise Invalid(
                "the pool is full; a slow-drip attacker holding "
                "slots is why this is not just bad luck"
            )
        if self._by_source(source) >= PER_SOURCE_CAP:
            self.rejected_for_cap += 1
            return (
                f"{source} refused: already holds "
                f"{PER_SOURCE_CAP} slots, and one source may "
                "not occupy the whole pool"
            )
        self.active[conn_id] = Connection(
            conn_id=conn_id,
            source=source,
            opened_at=now,
            last_progress_at=now,
        )
        return f"{conn_id} opened"

    def progress(
        self, conn_id: str, new_bytes: int, now: int
    ) -> str:
        conn = self.active.get(conn_id)
        if conn is None:
            raise Invalid(f"{conn_id} is not open")
        if new_bytes <= 0:
            return f"{conn_id}: no progress, the clock keeps running"
        conn.bytes_seen += new_bytes
        conn.last_progress_at = now
        return f"{conn_id}: {conn.bytes_seen} bytes, clock reset"

    def reap(self, now: int) -> list[str]:
        reaped = []
        for conn_id, conn in list(self.active.items()):
            if now - conn.last_progress_at >= PROGRESS_DEADLINE:
                del self.active[conn_id]
                self.stall_reaps += 1
                reaped.append(
                    f"{conn_id} from {conn.source} reaped: no "
                    f"progress in {now - conn.last_progress_at} "
                    "tick(s), the slow-drip signature"
                )
        return reaped

    def close(self, conn_id: str) -> str:
        if conn_id not in self.active:
            raise Invalid(f"{conn_id} is not open")
        del self.active[conn_id]
        self.normal_closes += 1
        return f"{conn_id} closed normally"

    def defense_report(self) -> str:
        return (
            f"{self.stall_reaps} stall-reap(s), "
            f"{self.normal_closes} normal close(s), "
            f"{self.rejected_for_cap} per-source rejection(s); "
            "a spike in stall-reaps is the attack's signature, "
            "and a defense that cannot show it is guessing"
        )
