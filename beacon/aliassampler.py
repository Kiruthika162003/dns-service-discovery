"""Vose's alias method: draw from a weighted distribution in constant time per sample.

Sampling one outcome from n weighted choices sounds like it needs a
scan or a binary search over cumulative weights, costing time that
grows with n on every single draw. Vose's alias method pays that cost
once, at setup, and then draws each sample in constant time no matter
how many outcomes there are, which is what makes it the right tool when
millions of samples come from the same fixed distribution, as in load
generators, Monte Carlo runs, or weighted request routing. The setup
builds two tables. It scales the probabilities so their average is one,
then repeatedly pairs an outcome below average with one above it: the
small outcome fills its column up to full with a slice of the large
one, and the large one's leftover is fed back to be paired again. Each
column ends holding one outcome and an alias, so a draw is just picking
a column uniformly and then flipping a biased coin to keep the column's
own outcome or fall through to its alias. This module separates the
deterministic core, building the tables and resolving one draw from a
column and a coin value, from a small seeded sampler built on top, so
the arithmetic can be tested without depending on a stream of random
numbers. It refuses an empty or negative weighting, since neither
describes a distribution to sample from.
"""

from __future__ import annotations

import random

from beacon.errors import Invalid


def build(weights: list[float]) -> tuple[list[float], list[int]]:
    n = len(weights)
    if n == 0:
        raise Invalid("no weights were given; there is no distribution to build")
    total = 0.0
    for index, weight in enumerate(weights):
        if weight < 0:
            raise Invalid(
                f"weight at position {index} is {weight}; a weight cannot be "
                "negative"
            )
        total += weight
    if total <= 0:
        raise Invalid(
            "the weights sum to zero; at least one outcome must have positive "
            "weight"
        )
    scaled = [weight * n / total for weight in weights]
    alias = [0] * n
    probability = [0.0] * n
    small: list[int] = []
    large: list[int] = []
    for index, value in enumerate(scaled):
        (small if value < 1.0 else large).append(index)
    while small and large:
        low = small.pop()
        high = large.pop()
        probability[low] = scaled[low]
        alias[low] = high
        scaled[high] = scaled[high] - (1.0 - scaled[low])
        (small if scaled[high] < 1.0 else large).append(high)
    for leftover in large:
        probability[leftover] = 1.0
    for leftover in small:
        probability[leftover] = 1.0
    return probability, alias


def pick(probability: list[float], alias: list[int], column: int, coin: float) -> int:
    if not 0 <= column < len(probability):
        raise Invalid(
            f"column {column} is outside the range 0 to {len(probability) - 1}"
        )
    if coin < probability[column]:
        return column
    return alias[column]


class Sampler:
    def __init__(self, weights: list[float], seed: int | None = None) -> None:
        self._probability, self._alias = build(weights)
        self._size = len(weights)
        self._random = random.Random(seed)

    def sample(self) -> int:
        column = self._random.randrange(self._size)
        coin = self._random.random()
        return pick(self._probability, self._alias, column, coin)

    def sample_many(self, count: int) -> list[int]:
        if count < 0:
            raise Invalid(f"cannot draw {count} samples; the count cannot be negative")
        return [self.sample() for _ in range(count)]
