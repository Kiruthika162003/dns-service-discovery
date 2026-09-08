"""Gossip convergence: a rumor reaches everyone in logarithmic rounds, but the last few lag.

Gossip spreads information by having each node that knows a fact tell
a few others each round, and the reason it scales to enormous
clusters is that the number of nodes that know grows multiplicatively:
if each knowing node infects a fanout of new nodes per round, the
infected population roughly multiplies each round, so the rounds to
reach everyone grow only with the logarithm of the cluster size, not
the size itself. A cluster ten times larger needs only a couple more
rounds. The module computes that growth and surfaces the tail that
the clean logarithm hides. Early rounds are fast because almost every
contact reaches a new node, but the last stragglers are slow, since
by then almost every contact lands on a node that already knows, a
coupon-collector effect, so full convergence takes a few more rounds
than the naive logarithm suggests and, strictly, is probabilistic:
most nodes learn quickly, the final few slowly. The module simulates
the infection round by round under a deterministic multiplicative
model, reports the rounds to reach full coverage and the coverage
after a given number of rounds, so both the logarithmic speed and the
slow tail are numbers an operator can plan around.
"""

from __future__ import annotations

from beacon.errors import Invalid


def coverage_after(nodes: int, fanout: int, rounds: int) -> int:
    if nodes < 1:
        raise Invalid("a cluster needs at least one node")
    if fanout < 1:
        raise Invalid("a fanout below one never spreads the rumor")
    if rounds < 0:
        raise Invalid("a negative number of rounds is not time")
    infected = 1
    for _ in range(rounds):
        infected = min(nodes, infected + infected * fanout)
        if infected >= nodes:
            return nodes
    return infected


def rounds_to_converge(nodes: int, fanout: int) -> int:
    rounds = 0
    while coverage_after(nodes, fanout, rounds) < nodes:
        rounds += 1
    return rounds
