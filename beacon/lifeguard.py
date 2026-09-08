"""SWIM Lifeguard: a node that is itself struggling should be slower to accuse its peers.

SWIM detects a failed member by failing to get an ack to a probe,
but that signal is noisy: a probe can go unanswered because the
target is dead, or because the prober itself is overloaded, its
scheduler starved, its own packets delayed. A naive detector
blames the target either way and floods the cluster with false
suspicions exactly when it is least able to judge, during its own
distress. Lifeguard, the refinement HashiCorp added, gives each
node a local health multiplier that rises when the node misses
acks it expected and falls when things go smoothly, and it scales
its own probe and suspicion timeouts by that multiplier, so a
node that is struggling waits longer before concluding a peer is
gone. The insight is that the accuser's own health should temper
its accusations: a healthy node judges quickly, a distressed one
judges cautiously, and the multiplier is bounded so a permanently
sick node cannot stretch its timeouts to infinity and stop
detecting real failures altogether.
"""

from __future__ import annotations

from beacon.errors import Invalid


class Lifeguard:
    def __init__(self, max_multiplier: int = 8) -> None:
        if max_multiplier < 1:
            raise Invalid(
                "the multiplier ceiling must be at least one; a "
                "ceiling of zero would forbid even the base timeout"
            )
        self.max_multiplier = max_multiplier
        self.lhm = 0

    def on_missed_ack(self) -> None:
        self.lhm = min(self.max_multiplier, self.lhm + 1)

    def on_clean_probe(self) -> None:
        self.lhm = max(0, self.lhm - 1)

    def scaled_timeout(self, base_ms: int) -> int:
        return base_ms * (1 + self.lhm)

    def is_healthy(self) -> bool:
        return self.lhm == 0
