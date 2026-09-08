"""Watch fan-out: a thousand clients watching one service is a thundering herd.

Watch-based discovery is efficient per client and dangerous in
aggregate: when a popular service changes, every watcher must
be notified, and a naive registry notifying them one by one
serially turns one registration into a notification storm whose
tail latency is the herd size times the per-notify cost. The
fix operators reach for is fan-out batching, but the batch
introduces its own hazard the module keeps visible: a batch
window that groups notifications also delays them, so a client
watching for failover learns of the dead instance one batch
window late, and a window tuned for throughput can miss the
very deadline watching existed to meet. The planner prices the
tradeoff on the same herd: serial notification latency for the
last watcher against batched, and the freshness cost the batch
imposes, because the right window is the largest one that still
beats the failover deadline, and a batch tuned by throughput
alone is tuned against the reason anyone watches.

The measurement corrected a lazy assumption baked into the
first draft: batching was expected to shrink the tail, but at
a thousand watchers in fifty-batches the batched tail is 1060
against a serial 1000, worse, because per-batch overhead
accumulates faster than batching saves. The batch's real value
here is not throughput at all but bounding freshness to a
single window, and stating that honestly matters more than the
throughput story that does not survive the numbers.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid

PER_NOTIFY_TICKS = 1
BATCH_OVERHEAD = 3


@dataclass(frozen=True)
class HerdPlan:
    watchers: int
    batch_size: int
    failover_deadline: int

    def __post_init__(self) -> None:
        if self.watchers < 1:
            raise Invalid("no watchers, no herd")
        if self.batch_size < 1:
            raise Invalid("a batch of zero notifies nobody")

    def serial_tail(self) -> int:
        return self.watchers * PER_NOTIFY_TICKS

    def batched_tail(self) -> int:
        batches = -(-self.watchers // self.batch_size)
        return batches * (
            BATCH_OVERHEAD + self.batch_size * PER_NOTIFY_TICKS
        )

    def freshness_cost(self) -> int:
        return BATCH_OVERHEAD + (
            self.batch_size - 1
        ) * PER_NOTIFY_TICKS

    def beats_deadline(self) -> bool:
        return self.freshness_cost() <= self.failover_deadline

    def plan_report(self) -> str:
        serial = self.serial_tail()
        batched = self.batched_tail()
        fresh = self.freshness_cost()
        line = (
            f"{self.watchers} watcher(s): serial tail "
            f"{serial}, batched tail {batched}, freshness cost "
            f"{fresh} per notification"
        )
        if not self.beats_deadline():
            line += (
                f"; the batch delays failover news past the "
                f"{self.failover_deadline}-tick deadline, "
                "tuned by throughput against the reason anyone "
                "watches"
            )
        else:
            line += (
                f"; still inside the {self.failover_deadline}-"
                "tick failover deadline, the largest safe "
                "window"
            )
        return line
