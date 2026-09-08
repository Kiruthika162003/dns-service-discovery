"""CFS virtual runtime: always run the task furthest behind its fair share.

The completely fair scheduler approximates an ideal processor that
runs every task at once at a fraction of speed, by tracking for each
task a virtual runtime, the CPU time it has consumed scaled by its
weight, and always running the task with the smallest virtual
runtime, the one that has fallen furthest behind its fair share.
When a task runs, its virtual runtime advances by the actual time it
ran times a ratio that shrinks with its weight, so a heavier task's
virtual clock ticks slower and it is therefore chosen more often to
keep its real share proportional to its weight. Two consequences fall
out and the module surfaces them. Weights map directly to CPU share,
since the vruntime scaling is the only thing distinguishing tasks.
And a newly woken task must not be admitted with a virtual runtime of
zero, because a stale zero would be far below everyone else's and the
task would monopolize the CPU until it caught up, so a new task is
placed at the current minimum virtual runtime instead, joining fairly
rather than starving the others. The module runs a task and charges
its weighted vruntime, picks the minimum, and admits a new task at the
current minimum, refusing a non-positive weight.
"""

from __future__ import annotations

from beacon.errors import Invalid

_BASE_WEIGHT = 1024


class CFS:
    def __init__(self) -> None:
        self.vruntime: dict[str, float] = {}
        self.weight: dict[str, int] = {}

    def add(self, task: str, weight: int) -> None:
        if weight <= 0:
            raise Invalid("a task needs a positive weight to have a share")
        self.weight[task] = weight
        self.vruntime[task] = min(self.vruntime.values(), default=0.0)

    def pick(self) -> str:
        if not self.vruntime:
            raise Invalid("no runnable task to pick")
        return min(self.vruntime, key=lambda t: (self.vruntime[t], t))

    def run(self, task: str, actual: float) -> None:
        if task not in self.weight:
            raise Invalid(f"{task} is not a runnable task")
        self.vruntime[task] += actual * (_BASE_WEIGHT / self.weight[task])
