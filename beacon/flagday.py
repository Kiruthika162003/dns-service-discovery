"""DNS flag day: stop nursing broken servers, and let the whole system get simpler and faster.

For years resolvers carried elaborate workarounds for
authoritative servers that mishandled EDNS: send a modern query,
get silence, and instead of giving up, retry with EDNS stripped,
then retry again with smaller options, a cascade of fallbacks that
turned one broken server into several slow round trips on every
resolution that touched it. The workarounds worked, and that was
the problem, because they hid the brokenness from the operators
who could have fixed it and taxed every resolver with retries for
servers that should simply have been repaired. The DNS flag day
was the coordinated decision to stop. After it, a server that does
not answer a standard EDNS query is treated as broken, not
humored: the resolver returns SERVFAIL rather than retrying
without EDNS, which is faster, simpler, and finally puts the cost
back on the broken server's operator. The module models the two
regimes so the trade is explicit, the pre-flag-day retry that
tolerated broken servers at the cost of a slow path, and the
post-flag-day failure that refuses to.
"""

from __future__ import annotations

from beacon.errors import Invalid

EDNS_STATES = ("ok", "no-response", "malformed")


def resolve_behavior(edns_response: str, pre_flag_day: bool) -> str:
    if edns_response not in EDNS_STATES:
        raise Invalid(
            f"{edns_response!r} is not an EDNS response state; it "
            f"knows {', '.join(EDNS_STATES)}"
        )
    if edns_response == "ok":
        return "answer"
    if pre_flag_day:
        return "retry-without-edns"
    return "servfail"


def retries_saved(broken_servers: int, pre_flag_day: bool) -> int:
    if pre_flag_day:
        return 0
    return broken_servers
