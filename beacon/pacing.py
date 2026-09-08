"""Packet pacing: spread a window over the round trip instead of dumping it in a burst.

A sender allowed a congestion window of packets can transmit them any
way it likes within a round trip, and the naive way, sending the
whole window at once the moment it is granted, creates a microburst
that slams a shallow router buffer and can overflow it, causing the
very loss the window was sized to avoid. Pacing spreads the window
evenly instead. It computes an inter-packet interval of the round
trip divided by the window, so the packets leave at a steady rate of
window-over-RTT rather than in a clump, and the buffers along the
path see a smooth trickle they can absorb rather than a spike they
must either queue deeply or drop. The benefit is fewer drops and
lower queueing delay from smoother traffic, and the cost is a little
latency for the packets that could have gone immediately but now wait
their turn in the pacing schedule, a small delay traded for far fewer
retransmits. Modern stacks pace by default for this reason. The
module computes the inter-packet interval from a window and a round
trip, and identifies the bursting case where a whole window is sent
at once, refusing a non-positive window or round trip that describes
no sending rate.
"""

from __future__ import annotations

from beacon.errors import Invalid


def inter_packet_interval(cwnd: int, rtt: float) -> float:
    if cwnd < 1:
        raise Invalid("a window below one packet sends nothing to pace")
    if rtt <= 0:
        raise Invalid("the round trip must be positive to define a rate")
    return rtt / cwnd


def paced_rate(cwnd: int, rtt: float) -> float:
    return cwnd / rtt if rtt > 0 else 0.0


def is_burst(sent_now: int, cwnd: int) -> bool:
    return sent_now >= cwnd
