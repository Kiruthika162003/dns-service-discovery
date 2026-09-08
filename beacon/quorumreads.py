"""Quorum reads: how many replicas must agree before an answer is trusted.

A replicated registry can answer from any replica, but any one
replica might be stale, so the read consistency knob is how
many replicas must agree. The arithmetic operators actually
need is the overlap rule: if writes go to W replicas and reads
consult R, then R plus W greater than the replica count
guarantees every read sees at least one replica that saw the
latest write, and a read set that does not satisfy it can miss
a write that already succeeded. The module computes whether a
given R, W, N triple is strongly consistent, and when a read
returns conflicting values, resolves by the version each
carries and reports how many replicas were behind, because the
count of stale replicas in a quorum is the early warning of a
replica falling out of sync before it drifts far enough to
fail a quorum outright. The honest tension it states: higher
R and W buy consistency and cost latency and availability,
and a system tuned for one without naming the other is tuned
by accident.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid


@dataclass(frozen=True)
class QuorumConfig:
    replicas: int
    read_quorum: int
    write_quorum: int

    def __post_init__(self) -> None:
        if self.replicas < 1:
            raise Invalid("a quorum needs replicas")
        if not 1 <= self.read_quorum <= self.replicas:
            raise Invalid(
                "the read quorum must be between 1 and the "
                "replica count"
            )
        if not 1 <= self.write_quorum <= self.replicas:
            raise Invalid(
                "the write quorum must be between 1 and the "
                "replica count"
            )

    def strongly_consistent(self) -> bool:
        return (
            self.read_quorum + self.write_quorum
            > self.replicas
        )

    def verdict(self) -> str:
        if self.strongly_consistent():
            return (
                f"R{self.read_quorum} + W{self.write_quorum} > "
                f"N{self.replicas}: every read overlaps the "
                "latest write, strongly consistent, paid for "
                "in latency and availability"
            )
        return (
            f"R{self.read_quorum} + W{self.write_quorum} <= "
            f"N{self.replicas}: a read can miss a write that "
            "already succeeded, eventually consistent whether "
            "you meant it or not"
        )


def resolve_read(
    responses: list[tuple[str, int]],
) -> tuple[str, int]:
    if not responses:
        raise Invalid("an empty quorum answered nothing")
    winner_value, winner_version = max(
        responses, key=lambda row: row[1]
    )
    stale = sum(
        1
        for _, version in responses
        if version < winner_version
    )
    return winner_value, stale


def read_report(
    config: QuorumConfig, responses: list[tuple[str, int]]
) -> str:
    if len(responses) < config.read_quorum:
        raise Invalid(
            f"only {len(responses)} replica(s) answered a "
            f"read quorum of {config.read_quorum}; the read "
            "cannot be trusted and must not pretend it can"
        )
    value, stale = resolve_read(responses)
    line = (
        f"read resolves to {value!r}; {stale} of "
        f"{len(responses)} replica(s) were behind"
    )
    if stale > 0:
        line += (
            "; the stale count is the early warning of a "
            "replica drifting before it fails a quorum outright"
        )
    return line
