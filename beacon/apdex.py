"""Apdex: compress a latency distribution into one number, at the cost of its shape.

Watching a latency distribution is hard because it is many numbers,
and Apdex reduces it to one an operator can trend and alert on. It
sorts each request into three buckets against a target latency: a
request answered within the target is satisfied, one answered within
four times the target is tolerating, and anything slower is
frustrated, and the score is the satisfied count plus half the
tolerating count over the total, a number from zero to one where one
is everyone satisfied and zero is everyone frustrated. The half-weight
on tolerating is the judgement baked in, that a slow-but-acceptable
response is worth half a good one. The compression is useful and the
module states its cost plainly: a single number hides the shape of
the distribution it came from, so two very different distributions
can score the same, a uniform spread of mediocre latencies and a
bimodal mix of fast and frustrated, which means Apdex is a summary to
trend, not a diagnosis to act on, and a dropping Apdex tells you
something changed without telling you what. The module classifies a
latency against the target, computes the score over a batch, and
reports the bucket counts, so the number and the distribution behind
it are both available.
"""

from __future__ import annotations

from beacon.errors import Invalid


def classify(latency: float, target: float) -> str:
    if target <= 0:
        raise Invalid("the Apdex target must be a positive latency")
    if latency <= target:
        return "satisfied"
    if latency <= 4 * target:
        return "tolerating"
    return "frustrated"


def score(latencies: list[float], target: float) -> float:
    if not latencies:
        raise Invalid("an empty sample has no Apdex score")
    satisfied = sum(1 for x in latencies if classify(x, target) == "satisfied")
    tolerating = sum(
        1 for x in latencies if classify(x, target) == "tolerating"
    )
    return (satisfied + tolerating / 2) / len(latencies)


def buckets(latencies: list[float], target: float) -> dict[str, int]:
    counts = {"satisfied": 0, "tolerating": 0, "frustrated": 0}
    for latency in latencies:
        counts[classify(latency, target)] += 1
    return counts
