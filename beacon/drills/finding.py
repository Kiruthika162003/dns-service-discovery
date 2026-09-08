"""A drill's verdict: the claim, the numbers, and whether they still agree."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    drill: str
    claim: str
    numbers: dict
    holds: bool

    def line(self) -> str:
        state = "holds" if self.holds else "BROKEN"
        return f"[{state}] {self.drill}: {self.claim}"
