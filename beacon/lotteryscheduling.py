"""Lottery scheduling: hold tickets, draw at random, so share is proportional in expectation.

Lottery scheduling allocates a resource by holding a drawing. Each
client holds a number of tickets in proportion to the share it should
get, and each scheduling decision draws a random ticket and runs its
holder, so over many draws a client that holds a third of the tickets
runs about a third of the time. Its appeal is simplicity and grace
under change: adding or removing a client is just adding or removing
tickets, with no per-client scheduling state to maintain, and
transient clients are handled naturally. The honest cost, against a
deterministic scheme like stride scheduling, is variance. Any single
draw is random, so over a short window a client can be lucky or
unlucky and get more or less than its proportion, and the guarantee
is only that the share converges in expectation over many draws.
Where short-term fairness matters that variance is a real drawback;
where only long-run share matters the simplicity wins. The module
resolves a draw over a ticket allocation to a winner by walking the
cumulative ticket counts, and computes a client's expected share, so
the proportionality and its probabilistic nature are both explicit,
refusing an out-of-range draw that names no ticket.
"""

from __future__ import annotations

from beacon.errors import Invalid


def total_tickets(allocation: dict[str, int]) -> int:
    return sum(allocation.values())


def winner(allocation: dict[str, int], draw: int) -> str:
    total = total_tickets(allocation)
    if total < 1:
        raise Invalid("no tickets to draw from")
    if not 0 <= draw < total:
        raise Invalid(
            f"the draw {draw} must name a ticket in 0..{total - 1}"
        )
    running = 0
    for client in sorted(allocation):
        running += allocation[client]
        if draw < running:
            return client
    raise Invalid("unreachable: the draw fell past every ticket")


def expected_share(allocation: dict[str, int], client: str) -> float:
    total = total_tickets(allocation)
    if total < 1:
        raise Invalid("no tickets held")
    return allocation.get(client, 0) / total
