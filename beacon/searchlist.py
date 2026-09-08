"""The search list: the shorthand that quietly multiplies every typo by four.

A developer types "db" and the stub resolver helpfully tries
db.team.corp.example, db.corp.example, db.example, and finally
db, and the convenience has three sharp edges this module
keeps visible. First, ndots: a name with enough dots is tried
as-is first, because payments.stripe.com should not tour the
internal suffixes before leaving the building, and the tour it
would otherwise take is counted. Second, the typo multiplier:
a nonexistent shorthand costs one NXDOMAIN per suffix, so the
census reports how many upstream queries each failed lookup
actually burned, which is how operators discover their login
storm is a search list amplifying a misconfigured hostname by
four. Third, the shadow hazard: a new internal name that
happens to match an earlier suffix expansion changes what an
existing shorthand resolves to without anyone editing
anything, and the checker names such collisions before the
surprise ships.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid

NDOTS = 2


@dataclass
class SearchList:
    suffixes: tuple[str, ...]
    expansions_tried: int = 0
    typo_burns: int = 0

    def __post_init__(self) -> None:
        if not self.suffixes:
            raise Invalid(
                "an empty search list is just absolute names "
                "with extra steps"
            )

    def candidates(self, shorthand: str) -> list[str]:
        dots = shorthand.count(".")
        expanded = [
            f"{shorthand}.{suffix}" for suffix in self.suffixes
        ]
        if dots >= NDOTS or shorthand.endswith("."):
            return [shorthand.rstrip("."), *expanded]
        return [*expanded, shorthand]

    def resolve_against(
        self, shorthand: str, existing: set[str]
    ) -> tuple[str | None, int]:
        tried = 0
        for candidate in self.candidates(shorthand):
            tried += 1
            self.expansions_tried += 1
            if candidate in existing:
                return candidate, tried
        self.typo_burns += tried
        return None, tried

    def typo_census(self) -> str:
        return (
            f"{self.expansions_tried} expansion(s) tried, "
            f"{self.typo_burns} burned on names that resolved "
            "nowhere; the login storm is often a search list "
            "amplifying one misconfigured hostname"
        )

    def shadow_check(
        self, new_name: str, shorthands: list[str]
    ) -> list[str]:
        collisions = []
        for shorthand in shorthands:
            candidates = self.candidates(shorthand)
            if new_name in candidates:
                position = candidates.index(new_name)
                collisions.append(
                    f"{shorthand} would now resolve to "
                    f"{new_name} (candidate {position + 1}); "
                    "an existing shorthand changed meaning "
                    "without anyone editing anything"
                )
        return collisions
