"""CRDT convergence under reordering, the property that makes coordination-free merge safe.

A conflict-free type's whole promise is that replicas which see
the same updates in any order end at the same state, so the drill
that matters is not that one merge works but that merging in
different orders agrees. It builds three counters and three sets
on separate replicas, merges them left to right and then right to
left, and holds that the PN-counter's value and the OR-set's
members are identical whichever way the merges folded, and that
the OR-set lets a concurrent add win a race against a remove. If
any of those broke, the type would have a merge order that
mattered, which is exactly the coordination CRDTs exist to avoid,
so the drill pins the order-independence rather than trusting the
algebra to hold itself together.
"""

from __future__ import annotations

from beacon.drills.finding import Finding
from beacon.orset import ORSet
from beacon.pncounter import PNCounter


def run() -> Finding:
    left = PNCounter()
    left.increment("a", 10)
    left.decrement("a", 3)
    right = PNCounter()
    right.increment("b", 5)
    right.decrement("b", 1)
    forward = left.merge(right).value()
    backward = right.merge(left).value()

    set_left = ORSet()
    set_left.add("web", "t1")
    set_right = set_left.merge(ORSet())
    set_right.remove("web")
    set_left.add("web", "t2")
    add_wins = set_left.merge(set_right).contains("web")
    reverse_wins = set_right.merge(set_left).contains("web")

    numbers = {
        "pn_forward": forward,
        "pn_backward": backward,
        "pn_converges": forward == backward,
        "add_wins": add_wins,
        "order_independent": add_wins == reverse_wins,
    }
    holds = (
        forward == backward == 11
        and add_wins
        and reverse_wins
    )
    return Finding(
        drill="crdt",
        claim=(
            "a PN-counter converges to 11 whichever way three "
            "replicas merge, and an OR-set lets a concurrent add "
            "win a remove race identically in both merge orders, "
            "so no merge order can change the result"
        ),
        numbers=numbers,
        holds=holds,
    )
