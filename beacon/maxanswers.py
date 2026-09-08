"""Answer set sizing: a hundred A records is a load balancer's worst tool.

A name backed by a hundred instances can return all hundred
addresses, and doing so is almost always wrong: the answer
overflows the datagram and forces TCP, most clients use only
the first address so the other ninety-nine are pure weight,
and the record set churns on every registration change,
busting caches fleet-wide. The sizer returns a bounded subset
chosen deterministically per query so the load still spreads,
with the size picked to fit the UDP budget rather than to
list the world. The measurement it keeps honest is the
coverage-versus-size tradeoff: a subset of K rotated across
queries still reaches all N instances over enough queries,
and the report states how many queries it takes to cover the
fleet at a given subset size, because a load balancer that
silently drops ninety instances from every answer owes the
operator the number of queries before the ninetieth is ever
seen.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from beacon.errors import Invalid

UDP_ANSWER_BUDGET = 6


@dataclass(frozen=True)
class AnswerSizer:
    instances: tuple[str, ...]
    subset_size: int = UDP_ANSWER_BUDGET

    def __post_init__(self) -> None:
        if not self.instances:
            raise Invalid("a name with no instances answers nothing")
        if self.subset_size < 1:
            raise Invalid("a subset of zero serves nobody")

    def answer_for(self, query_id: str) -> list[str]:
        if self.subset_size >= len(self.instances):
            return sorted(self.instances)
        rotor = int(
            hashlib.sha256(query_id.encode()).hexdigest()[:8],
            16,
        ) % len(self.instances)
        ordered = list(self.instances[rotor:]) + list(
            self.instances[:rotor]
        )
        return sorted(ordered[: self.subset_size])

    def queries_to_cover(self, query_ids: list[str]) -> int:
        seen: set[str] = set()
        for count, query_id in enumerate(query_ids, start=1):
            seen.update(self.answer_for(query_id))
            if len(seen) == len(self.instances):
                return count
        return -1

    def coverage_report(self, query_ids: list[str]) -> str:
        if len(self.instances) <= self.subset_size:
            return (
                f"{len(self.instances)} instance(s) fit one "
                f"answer of {self.subset_size}; no rotation "
                "needed and no instance hidden"
            )
        covered_at = self.queries_to_cover(query_ids)
        if covered_at < 0:
            return (
                f"{len(query_ids)} query(ies) did not cover "
                f"all {len(self.instances)} instance(s); some "
                "remain unseen, and a hidden instance is idle "
                "capacity nobody chose to idle"
            )
        return (
            f"subset {self.subset_size} of "
            f"{len(self.instances)}: the full fleet is first "
            f"seen after {covered_at} query(ies), which is the "
            "number a load balancer owes the operator before "
            "it hides ninety instances from every answer"
        )
