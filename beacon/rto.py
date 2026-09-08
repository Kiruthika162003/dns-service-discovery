"""Retransmission timeout: a smoothed RTT plus a variance margin, never sampling a retransmit.

Deciding how long to wait for an acknowledgement before assuming a
segment was lost is a balance: too short and the sender retransmits
segments that were merely slow, too long and it sits idle after a
real loss. The Jacobson/Karels estimator computes the timeout from
the round-trip times it observes. It keeps a smoothed round-trip
time, an exponentially weighted average, and a smoothed variation,
how much samples swing around that average, and sets the timeout to
the smoothed time plus four times the variation, so a jittery path
gets a generous margin and a steady one a tight timeout. The subtle
rule that keeps the estimate honest is Karn's algorithm: a
retransmitted segment must never contribute a round-trip sample,
because when an acknowledgement arrives for a segment sent twice
there is no way to know which send it answers, and mistaking the
retransmit's short interval for the original's would corrupt the
estimate downward and cause a cascade of premature timeouts. So the
module refuses a sample drawn from a retransmitted segment, updates
the smoothed time and variation from a clean sample, and computes the
timeout as the smoothed time plus four variations, clamped to a floor
so it never drops below a sane minimum.
"""

from __future__ import annotations

from beacon.errors import Invalid


class RtoEstimator:
    def __init__(self, alpha: float = 0.125, beta: float = 0.25) -> None:
        self.alpha = alpha
        self.beta = beta
        self.srtt: float | None = None
        self.rttvar = 0.0

    def sample(self, rtt: float, retransmitted: bool = False) -> None:
        if retransmitted:
            raise Invalid(
                "Karn's algorithm forbids sampling a retransmitted "
                "segment; the ACK is ambiguous about which send it "
                "answers, and the sample would corrupt the estimate"
            )
        if rtt < 0:
            raise Invalid("a round-trip time is never negative")
        if self.srtt is None:
            self.srtt = rtt
            self.rttvar = rtt / 2
            return
        self.rttvar = (1 - self.beta) * self.rttvar + self.beta * abs(
            self.srtt - rtt
        )
        self.srtt = (1 - self.alpha) * self.srtt + self.alpha * rtt

    def rto(self, minimum: float = 1.0) -> float:
        if self.srtt is None:
            raise Invalid("no sample yet; there is no RTT to time out on")
        return max(minimum, self.srtt + 4 * self.rttvar)
