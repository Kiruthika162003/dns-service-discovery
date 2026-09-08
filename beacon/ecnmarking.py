"""Explicit congestion notification: mark a packet to signal congestion instead of dropping it.

The traditional congestion signal is a dropped packet: a full queue
discards arrivals, the loss tells the sender to slow down, and the
lost packet is retransmitted. Explicit congestion notification offers
a gentler signal for senders that opt in. When a router's queue grows
past a marking threshold it sets a congestion-experienced mark on an
ECN-capable packet rather than dropping it, the receiver echoes the
mark back, and the sender reduces its window exactly as it would on a
loss, but without losing the packet or paying the retransmit. When
both ends support ECN this is strictly better than dropping: the same
congestion feedback arrives without the cost of the discarded packet.
Two things keep it honest, and the module encodes them. A packet from
a flow that is not ECN-capable cannot be marked and must still be
dropped when the queue demands it, and the marking threshold must sit
below the drop threshold, so the router marks before it is forced to
drop, or ECN never engages and the queue just overflows as before.
The module decides forward, mark, or drop from the queue depth, the
two thresholds, and whether the flow is ECN-capable, refusing
thresholds that are out of order.
"""

from __future__ import annotations

from beacon.errors import Invalid


def action(
    queue_depth: int,
    mark_threshold: int,
    drop_threshold: int,
    ecn_capable: bool,
) -> str:
    if mark_threshold >= drop_threshold:
        raise Invalid(
            "the mark threshold must sit below the drop threshold, or "
            "the router drops before it ever marks and ECN never "
            "engages"
        )
    if queue_depth < mark_threshold:
        return "forward"
    if queue_depth < drop_threshold and ecn_capable:
        return "mark"
    return "drop"
