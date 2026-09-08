"""Deterministic aperture: clients that place themselves on a shared ring load backends evenly.

When each client picks a random subset of backends to talk to, the
subsets overlap unevenly, and some backend ends up in far more
clients' subsets than another, so load skews even though every
client subsetted fairly. Deterministic aperture, from Finagle,
removes the randomness that causes the skew. Clients and backends
share one ordered ring, each client takes its position on it, and
its aperture is a contiguous run of backends starting from that
position, so the clients spread themselves around the ring and the
union of their apertures covers the backends evenly rather than by
luck. The determinism is the whole mechanism: because every client
computes the same ring the same way, their apertures interlock
instead of clumping, and per-backend load stays within a small
constant of even where random subsetting leaves a long tail of
overloaded and idle backends. The module computes the per-backend
client count under deterministic aperture and reports the spread,
so the evenness the shared ring buys is a measured number rather
than a claim.
"""

from __future__ import annotations

from beacon.errors import Invalid


def aperture_load(
    num_clients: int, num_backends: int, aperture: int
) -> list[int]:
    if num_clients < 1 or num_backends < 1:
        raise Invalid(
            "there must be at least one client and one backend to "
            "place on the ring"
        )
    if not 1 <= aperture <= num_backends:
        raise Invalid(
            f"an aperture of {aperture} must be between one and the "
            f"{num_backends} backends; wider than the ring is not a "
            "subset"
        )
    counts = [0] * num_backends
    for client in range(num_clients):
        start = (client * num_backends) // num_clients
        for step in range(aperture):
            counts[(start + step) % num_backends] += 1
    return counts


def spread(num_clients: int, num_backends: int, aperture: int) -> int:
    counts = aperture_load(num_clients, num_backends, aperture)
    return max(counts) - min(counts)
