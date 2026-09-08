"""Response rate limiting with slip: throttle a reflection flood without blackholing clients.

An authoritative server is a reflection weapon: an attacker spoofs a
victim's address as the source of a query, and the large response is
bounced at the victim, amplified. Rate limiting the responses defends
against it, but a blunt limiter that simply drops everything over the
rate also drops the legitimate clients who happen to share the
attacker's rate-limit bucket, a coarse client-prefix. Response rate
limiting adds a gentler mechanism, the slip. When identical responses
to a prefix exceed the limit, instead of dropping every excess one
the server occasionally, every slip-th time, sends a truncated
response rather than nothing. A truncated response tells a genuine
client to retry over TCP, which a real client can do and a spoofing
attacker cannot benefit from, since the truncated answer is tiny and
the victim never asked, so the amplification collapses while a real
client caught in the crossfire still has a path through. The slip
rate tunes the tradeoff between letting legitimate clients through
and denying the attacker any reflected volume. The module counts
responses per key and decides answer, truncate, or drop against the
limit and the slip, so the defense and its collateral are explicit.
"""

from __future__ import annotations

from beacon.errors import Invalid


class ResponseRateLimiter:
    def __init__(self, limit: int, slip: int) -> None:
        if limit < 1:
            raise Invalid("a limit below one answers nothing")
        if slip < 1:
            raise Invalid(
                "a slip of zero never sends a truncated response, so "
                "a real client caught over the limit gets no path "
                "through at all"
            )
        self.limit = limit
        self.slip = slip
        self.counts: dict[str, int] = {}

    def handle(self, key: str) -> str:
        self.counts[key] = self.counts.get(key, 0) + 1
        count = self.counts[key]
        if count <= self.limit:
            return "answer"
        over = count - self.limit
        if over % self.slip == 0:
            return "truncated"
        return "dropped"
