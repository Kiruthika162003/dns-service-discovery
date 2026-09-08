"""Reservoir sampling: a uniform sample of a stream whose length you do not know in advance.

Sampling query logs to keep a representative slice without storing
every line runs into a problem the moment the stream has no known
end: you cannot pick a uniform sample of N items from a stream if
you do not know how many items there will be. Reservoir sampling
solves it in a single pass with memory for only the sample. It keeps
the first k items outright, and then for the item at position i
beyond the first k it replaces a randomly chosen slot with
probability k over i, a probability that falls as the stream grows.
The arithmetic works out so that after any number of items every
item seen so far has exactly the same chance, k over the total, of
being in the sample, which is the uniformity the sample needs, and
it holds without ever knowing the total ahead of time. The cost,
stated plainly, is that it is a sample and not the whole stream, so
a rare event may simply not be picked, which is why reservoir
sampling is right for representative slices and wrong for catching
every outlier. The module fills the reservoir, applies the
decreasing-probability replacement from an injected draw so the
behavior is testable, and reports the running count that drives the
probability.
"""

from __future__ import annotations

from beacon.errors import Invalid


class Reservoir:
    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise Invalid("a reservoir of zero capacity samples nothing")
        self.capacity = capacity
        self.sample: list[str] = []
        self.seen = 0

    def offer(self, item: str, draw: float) -> None:
        if not 0.0 <= draw < 1.0:
            raise Invalid(
                f"the draw {draw} must be in [0, 1); it selects the "
                "slot to replace, it is not the slot"
            )
        self.seen += 1
        if len(self.sample) < self.capacity:
            self.sample.append(item)
            return
        index = int(draw * self.seen)
        if index < self.capacity:
            self.sample[index] = item

    def contents(self) -> list[str]:
        return list(self.sample)
