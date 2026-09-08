"""Power of two choices: one extra look, most of the crowding gone.

Random assignment sends every request to a backend chosen
blind, and blind choice stacks: some backend ends up carrying
far more than its share purely by luck. The two-choice rule
peeks at two random backends and takes the shorter queue, and
the theory's famous promise is that this one extra look
collapses the maximum load from a lottery to nearly flat. The
simulator makes the promise a measurement: the same
deterministic request stream, hashed two ways, assigned once
blind and once by comparison, with the maximum queue and the
spread reported side by side, because the two-choice rule is
the rare optimization whose benefit is so large that people
disbelieve it until the table sits in front of them. The
deliberately rigged third column runs choice-of-two where both
peeks land on the same backend, the degenerate case, to show
the benefit comes from the comparison and not from the second
hash.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from beacon.errors import Invalid


def _spot(key: str, salt: str, backends: int) -> int:
    digest = hashlib.sha256(f"{salt}|{key}".encode()).hexdigest()
    return int(digest[:8], 16) % backends


@dataclass
class LoadTable:
    strategy: str
    queues: list[int]

    def maximum(self) -> int:
        return max(self.queues)

    def spread(self) -> int:
        return max(self.queues) - min(self.queues)

    def line(self) -> str:
        return (
            f"{self.strategy}: max {self.maximum()}, spread "
            f"{self.spread()}"
        )


def assign_blind(requests: int, backends: int) -> LoadTable:
    if backends < 2 or requests < 1:
        raise Invalid(
            "the comparison needs two backends and some load"
        )
    queues = [0] * backends
    for number in range(requests):
        queues[_spot(f"r{number}", "one", backends)] += 1
    return LoadTable(strategy="blind", queues=queues)


def assign_two_choice(
    requests: int, backends: int
) -> LoadTable:
    if backends < 2 or requests < 1:
        raise Invalid(
            "the comparison needs two backends and some load"
        )
    queues = [0] * backends
    for number in range(requests):
        first = _spot(f"r{number}", "one", backends)
        second = _spot(f"r{number}", "two", backends)
        chosen = (
            first
            if queues[first] <= queues[second]
            else second
        )
        queues[chosen] += 1
    return LoadTable(strategy="two-choice", queues=queues)


def assign_degenerate(
    requests: int, backends: int
) -> LoadTable:
    queues = [0] * backends
    for number in range(requests):
        spot = _spot(f"r{number}", "one", backends)
        queues[spot] += 1
    return LoadTable(strategy="degenerate", queues=queues)


def comparison_table(requests: int, backends: int) -> str:
    blind = assign_blind(requests, backends)
    smart = assign_two_choice(requests, backends)
    rigged = assign_degenerate(requests, backends)
    return "\n".join(
        [
            f"{requests} request(s), {backends} backend(s):",
            f"  {blind.line()}",
            f"  {smart.line()}",
            f"  {rigged.line()} (both peeks on one backend: "
            "the benefit is the comparison, not the second "
            "hash)",
        ]
    )
