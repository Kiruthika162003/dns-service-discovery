"""Checkpoint frequency: shrink the recovery replay window, or spare the steady-state overhead.

A durable store recovers from a crash by replaying its log from the
last checkpoint, so how often it checkpoints sets a direct trade
between two costs. Checkpoint often and the log to replay after a
crash is short, so recovery is fast, but each checkpoint does work,
flushing state, possibly stalling writes, and doing it constantly
taxes the steady state when no crash is happening, which is almost
always. Checkpoint rarely and the steady-state overhead nearly
vanishes, but a crash then faces a long log to replay and a slow
recovery, exactly when the system most needs to be back. The right
interval balances the recovery-time objective, how long a restart may
take, against the overhead the workload can spare, and neither
extreme is free: the recovery cost is the interval times the write
rate, since that is how much log accumulates between checkpoints, and
the overhead is the checkpoint's cost spread over the interval. The
module computes the replay work a given interval implies and the
steady-state overhead fraction it imposes, so the interval is chosen
against measured numbers, the replay a crash would face and the tax
paid every second it does not, rather than by feel.
"""

from __future__ import annotations

from beacon.errors import Invalid


def replay_work(checkpoint_interval: float, write_rate: float) -> float:
    if checkpoint_interval <= 0 or write_rate < 0:
        raise Invalid(
            "the interval must be positive and the write rate "
            "non-negative"
        )
    return checkpoint_interval * write_rate


def overhead_fraction(
    checkpoint_cost: float, checkpoint_interval: float
) -> float:
    if checkpoint_interval <= 0:
        raise Invalid("the checkpoint interval must be positive")
    if checkpoint_cost < 0:
        raise Invalid("a checkpoint cost is never negative")
    return checkpoint_cost / checkpoint_interval
