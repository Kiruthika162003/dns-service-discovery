"""Deterministic subsetting: every client sees a few backends, together they see all.

A thousand clients each holding connections to three hundred
backends is a connection matrix nobody can afford, so each
client gets a subset. The two failure modes are both about
luck: random subsets leave some backend in nobody's subset,
starved of traffic while its peers drown, and naive
round-robin subsetting gives adjacent clients nearly identical
subsets, so one rack failure takes out the same backends for
everyone at once. Deterministic subsetting shuffles the
backend list with the client's own identity as the permutation
seed and takes a contiguous slice, which makes every client's
subset stable across restarts, cheap to compute anywhere, and
different from its neighbor's. The coverage report is the
honest half: it counts how many clients each backend appears
for, names the starved and the crowded, and measures the
spread, because subsetting trades connection count for balance
and the trade needs its price tag read aloud.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from beacon.errors import Invalid


def _permute(backends: list[str], seed: str) -> list[str]:
    return sorted(
        backends,
        key=lambda name: hashlib.sha256(
            f"{seed}|{name}".encode()
        ).hexdigest(),
    )


@dataclass(frozen=True)
class SubsetPlan:
    backends: tuple[str, ...]
    subset_size: int

    def __post_init__(self) -> None:
        if self.subset_size < 1:
            raise Invalid("a subset of nothing serves nothing")
        if self.subset_size > len(self.backends):
            raise Invalid(
                f"a subset of {self.subset_size} from "
                f"{len(self.backends)} backend(s) is just the "
                "whole list wearing a smaller name"
            )

    def subset_for(self, client_id: str) -> list[str]:
        shuffled = _permute(list(self.backends), client_id)
        return sorted(shuffled[: self.subset_size])

    def stable_across_restarts(self, client_id: str) -> bool:
        return self.subset_for(client_id) == self.subset_for(
            client_id
        )

    def coverage_report(self, clients: list[str]) -> str:
        if not clients:
            raise Invalid("coverage needs clients")
        seen_by: dict[str, int] = dict.fromkeys(self.backends, 0)
        for client in clients:
            for backend in self.subset_for(client):
                seen_by[backend] += 1
        starved = sorted(
            name for name, count in seen_by.items() if count == 0
        )
        heaviest = max(seen_by.values())
        lightest = min(seen_by.values())
        lines = [
            f"{len(clients)} client(s) x {self.subset_size} "
            f"of {len(self.backends)} backend(s): heaviest "
            f"backend seen by {heaviest}, lightest by "
            f"{lightest}"
        ]
        if starved:
            lines.append(
                f"  STARVED: {', '.join(starved)} appear in "
                "nobody's subset; their peers drown while "
                "they idle"
            )
        else:
            lines.append(
                "  every backend is in someone's subset; the "
                "trade's price tag, read aloud"
            )
        return "\n".join(lines)

    def neighbor_overlap(
        self, client_a: str, client_b: str
    ) -> int:
        return len(
            set(self.subset_for(client_a))
            & set(self.subset_for(client_b))
        )
