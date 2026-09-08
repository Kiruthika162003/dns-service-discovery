"""A surge queue: absorb a brief spike by queuing, shed a sustained overload by rejecting.

A server with a concurrency limit has to decide what to do with
requests that arrive while it is already at the limit, and both
extremes are wrong. Rejecting them immediately turns a brief harmless
spike into errors, since the burst would have drained in a moment.
Queuing them without bound turns a sustained overload into unbounded
latency, as the queue grows and every request waits longer behind a
line that never shortens, until the latency itself is the outage. A
surge queue takes the middle path. It runs requests up to the
concurrency limit, queues additional requests up to a bounded surge
depth so a short spike is absorbed and served as capacity frees, and
rejects, sheds, requests that arrive when even the queue is full, so a
sustained overload is converted into prompt rejection rather than
ever-growing delay. The bound on the queue is the key decision: it is
how much burst the server will absorb before it starts saying no, and
setting it trades a little tolerated latency for a firm ceiling on how
bad that latency can get. The module admits a request as run, queued,
or shed against the concurrency limit and the surge depth, promotes a
queued request when capacity frees, and completes one, so the spike-
absorb and overload-shed behaviors are both explicit.
"""

from __future__ import annotations

from beacon.errors import Invalid, Refused


class SurgeQueue:
    def __init__(self, concurrency: int, surge_depth: int) -> None:
        if concurrency < 1:
            raise Invalid("a concurrency of zero runs nothing")
        if surge_depth < 0:
            raise Invalid("a negative surge depth is not a queue")
        self.concurrency = concurrency
        self.surge_depth = surge_depth
        self.active = 0
        self.queued = 0

    def admit(self) -> str:
        if self.active < self.concurrency:
            self.active += 1
            return "run"
        if self.queued < self.surge_depth:
            self.queued += 1
            return "queued"
        raise Refused(
            "the surge queue is full; a sustained overload is shed "
            "as prompt rejection rather than unbounded latency"
        )

    def start_queued(self) -> None:
        if self.queued == 0:
            raise Invalid("no queued request to start")
        if self.active >= self.concurrency:
            raise Invalid(
                "no free capacity to start a queued request; a slot "
                "must complete first"
            )
        self.queued -= 1
        self.active += 1

    def complete(self) -> None:
        if self.active == 0:
            raise Invalid("no active request to complete")
        self.active -= 1
