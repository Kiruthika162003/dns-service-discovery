"""Earliest deadline first: run the task whose deadline is nearest, optimal on one processor.

When tasks carry deadlines, earliest-deadline-first scheduling always
runs the ready task whose absolute deadline is soonest, and on a
single processor it is optimal in a strong sense: if any scheduling
order could meet all the deadlines, EDF does. Its schedulability test
is correspondingly simple, the total utilization, the sum of each
task's compute time over its period, must not exceed one, meaning the
work fits in the time available, and if it does EDF meets every
deadline. That optimality and that clean bound are EDF's appeal
against fixed-priority schemes, which meet deadlines only up to a
lower utilization. The cost the module notes is behavior under
overload. EDF is dynamic, deadlines are recomputed as tasks arrive,
and when the system is overloaded, utilization above one, it degrades
unpredictably: a single task that overruns can cause a cascade of
missed deadlines across unrelated tasks, where a static-priority
scheme fails predictably, always sacrificing the lowest-priority task
first. The module picks the ready task with the nearest deadline,
breaking ties deterministically, and decides schedulability from the
utilization, refusing a negative utilization that describes no load.
"""

from __future__ import annotations

from beacon.errors import Invalid


def next_task(tasks: list[tuple[str, int]]) -> str:
    if not tasks:
        raise Invalid("no ready task to schedule")
    return min(tasks, key=lambda t: (t[1], t[0]))[0]


def schedulable(utilization: float) -> bool:
    if utilization < 0:
        raise Invalid("utilization is never negative")
    return utilization <= 1.0
