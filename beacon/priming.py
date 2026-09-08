"""Priming: trust the shipped root hints only far enough to ask the roots who they are.

A resolver ships with a root hints file, the list of root name
servers, but that file ages: roots are renumbered and added over
the years, and a resolver that trusted a stale hints file
forever would slowly drift away from the live root set. Priming
resolves the tension without a config edit. On start the
resolver uses the hints for one purpose only, to send a single
NS query for the root, and it trusts the authoritative answer
that comes back over its own hardcoded list, so the hints are a
bootstrap and not a source of truth. The rule the module keeps
is that a hint absent from the authoritative answer is dropped
and a new authoritative server is adopted, because the whole
point of priming is that the live root set overrides the file. A
resolver that clung to a decommissioned root because its hints
still named it would keep dialing a server that is gone, and the
one refusal is to prime from an empty answer, since a failed
priming that adopted nothing would strand the resolver with no
roots at all.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid


@dataclass(frozen=True)
class PrimingResult:
    adopted: frozenset[str]
    dropped: frozenset[str]
    added: frozenset[str]

    def summary(self) -> str:
        return (
            f"primed to {len(self.adopted)} roots: dropped "
            f"{len(self.dropped)} stale, adopted "
            f"{len(self.added)} new; the live root set overrides "
            "the shipped hints"
        )


def prime(
    hints: set[str], authoritative: set[str]
) -> PrimingResult:
    if not authoritative:
        raise Invalid(
            "priming returned no roots; the resolver keeps its "
            "hints rather than adopt an empty set that would "
            "strand it with no roots at all"
        )
    adopted = frozenset(authoritative)
    dropped = frozenset(hints - authoritative)
    added = frozenset(authoritative - hints)
    return PrimingResult(adopted, dropped, added)
