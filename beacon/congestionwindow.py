"""TCP congestion control: ramp fast to find capacity, then probe gently and retreat on loss.

A sender that does not know the network's capacity must discover it
without overwhelming it, and TCP does this with a congestion window
that governs how much may be in flight, grown and shrunk by two
regimes. Slow start, despite the name, grows the window aggressively,
doubling it each round trip, so the sender climbs quickly toward the
available bandwidth from a cautious initial value. Once the window
reaches a threshold, the estimate of where trouble began, it switches
to congestion avoidance and grows only additively, one segment per
round trip, probing for a little more capacity gently rather than
doubling into congestion. When loss signals congestion the window is
cut multiplicatively, the threshold dropped to half the current
window and the window reduced sharply, so the sender retreats fast
from an overloaded network. This additive-increase, multiplicative-
decrease rhythm is what makes many TCP flows share a link fairly and
stably: everyone probes up slowly and backs off hard, so no flow runs
away with the link for long. The module advances the window on an ack
under whichever regime applies and cuts it on loss, so the ramp, the
gentle probe, and the retreat are all explicit.
"""

from __future__ import annotations

from beacon.errors import Invalid


class CongestionWindow:
    def __init__(self, initial: int = 1, ssthresh: int = 16) -> None:
        if initial < 1 or ssthresh < 1:
            raise Invalid(
                "the window and threshold start at one or more; a "
                "window of zero sends nothing"
            )
        self.cwnd = initial
        self.ssthresh = ssthresh

    def on_ack(self) -> int:
        if self.cwnd < self.ssthresh:
            self.cwnd *= 2
        else:
            self.cwnd += 1
        return self.cwnd

    def on_loss(self) -> int:
        self.ssthresh = max(1, self.cwnd // 2)
        self.cwnd = 1
        return self.cwnd

    def in_slow_start(self) -> bool:
        return self.cwnd < self.ssthresh
