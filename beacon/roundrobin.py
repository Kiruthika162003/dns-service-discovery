"""Round-robin rotation: the answer list turns so the first slot is shared.

Most clients use the first address in the answer and ignore
the rest, which turns record order into load policy whether
anyone meant it or not. Rotation shares the first slot by
rotating the list one position per answer, and the module is
honest about what that buys and what it cannot: rotation
balances only across queries that miss the cache, because a
cached answer freezes one ordering for its whole TTL and
every client hitting that cache in the window sees the same
first address. The measurement makes the ceiling visible,
first-slot counts with rotation against rotation-behind-a-
cache, where the TTL decides everything: a long TTL hands one
lucky address nearly the whole window, which is why load
balancing by DNS rotation alone is a promise the cache
quietly breaks, and why the serious traffic goes through the
weighted wheel instead.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid


@dataclass
class Rotor:
    addresses: tuple[str, ...]
    position: int = 0
    first_slot_counts: dict[str, int] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if len(self.addresses) < 2:
            raise Invalid(
                "rotation needs at least two addresses; one "
                "address rotates into itself forever"
            )

    def answer(self) -> list[str]:
        ordered = list(
            self.addresses[self.position :]
        ) + list(self.addresses[: self.position])
        self.position = (self.position + 1) % len(
            self.addresses
        )
        first = ordered[0]
        self.first_slot_counts[first] = (
            self.first_slot_counts.get(first, 0) + 1
        )
        return ordered

    def share_table(self) -> str:
        total = sum(self.first_slot_counts.values())
        lines = [f"{total} answer(s), first slot shared:"]
        for address in self.addresses:
            count = self.first_slot_counts.get(address, 0)
            lines.append(f"  {address}: {count}")
        return "\n".join(lines)


def behind_a_cache(
    rotor: Rotor, queries: int, ttl: int
) -> dict[str, int]:
    if queries < 1 or ttl < 1:
        raise Invalid("the simulation needs queries and a ttl")
    first_seen: dict[str, int] = {}
    cached: list[str] | None = None
    cached_at = -ttl
    for tick in range(queries):
        if cached is None or tick - cached_at >= ttl:
            cached = rotor.answer()
            cached_at = tick
        first = cached[0]
        first_seen[first] = first_seen.get(first, 0) + 1
    return first_seen


def ceiling_report(
    addresses: tuple[str, ...], queries: int, ttl: int
) -> str:
    naked = Rotor(addresses=addresses)
    for _ in range(queries):
        naked.answer()
    naked_max = max(naked.first_slot_counts.values())
    cached_rotor = Rotor(addresses=addresses)
    seen = behind_a_cache(cached_rotor, queries, ttl)
    cached_max = max(seen.values())
    return (
        f"{queries} queries over {len(addresses)} addresses: "
        f"naked rotation tops out at {naked_max} first-slots, "
        f"behind a ttl-{ttl} cache one address takes "
        f"{cached_max}; the cache quietly breaks the promise, "
        "which is why serious traffic uses the weighted wheel"
    )
