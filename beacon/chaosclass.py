"""CHAOS-class queries: the server's own name and version, and why you might not give them out.

Beside the ordinary internet class, DNS carries a small CHAOS
class whose famous names, version.bind, hostname.bind, and
id.server, let an operator ask a server to describe itself, which
is handy for debugging a farm of anycast instances and dangerous
as a gift to an attacker. version.bind in particular returns the
exact software and version string, which is free reconnaissance: a
scanner that reads it knows precisely which published
vulnerabilities to try, so many operators disable or obfuscate the
answer, trading a little debugging convenience for denying the
fingerprint. id.server has the opposite pull, since telling which
physical instance answered is exactly what an operator debugging
anycast wants, so the sensible policy is per-name rather than
blanket. The module answers a CHAOS query under an explicit
disclosure policy, returns the real value only when disclosure for
that name is enabled and an obfuscated placeholder otherwise, and
refuses a name outside the known CHAOS set, since inventing an
answer for an unknown self-describing query is how a leak sneaks
back in under a name nobody audited.
"""

from __future__ import annotations

from beacon.errors import Invalid

CHAOS_NAMES = ("version.bind.", "hostname.bind.", "id.server.")


def answer(
    name: str,
    disclose: set[str],
    values: dict[str, str],
) -> str:
    if name not in CHAOS_NAMES:
        raise Invalid(
            f"{name} is not a known CHAOS name; the server "
            f"answers only {', '.join(CHAOS_NAMES)}, and inventing "
            "an answer for another is how a leak sneaks back in"
        )
    if name in disclose:
        return values.get(name, "")
    return "not disclosed"


def leaks_fingerprint(name: str, disclose: set[str]) -> bool:
    return name == "version.bind." and name in disclose
