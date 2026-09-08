"""Probabilistic early expiry: refresh a cache entry early, at random, so no herd forms.

A cache entry with a hard time-to-live creates a synchronized
stampede at the instant it expires: every reader that was being
served from it misses at the same moment and all of them rush
upstream to recompute the same value at once. Probabilistic early
recomputation, the XFetch algorithm, dissolves the synchrony by
letting each reader independently roll the dice as the expiry
approaches and, with a probability that rises the closer it gets,
decide to refresh the entry early on its own. Because the decision
is random and per-reader and the probability climbs smoothly toward
expiry, in practice a single reader triggers the refresh a little
before the hard deadline while everyone else keeps being served the
still-valid cached value, so the recompute happens once, ahead of
the cliff, instead of a thousand times at it. The trigger scales
with the estimated recompute cost, so expensive-to-rebuild entries
are refreshed earlier and with more margin than cheap ones. The
module implements the XFetch test from the recompute-cost estimate,
a tuning factor, and a random draw, and refuses a draw outside the
open unit interval on which its logarithm is defined.
"""

from __future__ import annotations

import math

from beacon.errors import Invalid


def should_refresh(
    now: float,
    expiry: float,
    recompute_cost: float,
    beta: float,
    draw: float,
) -> bool:
    if not 0.0 < draw <= 1.0:
        raise Invalid(
            f"the random draw {draw} must be in (0, 1]; its "
            "logarithm anchors the early-refresh window and is "
            "undefined at zero"
        )
    if recompute_cost < 0 or beta < 0:
        raise Invalid(
            "the recompute cost and tuning factor are never "
            "negative; they widen the early window, not narrow it "
            "below zero"
        )
    early = recompute_cost * beta * -math.log(draw)
    return now + early >= expiry
