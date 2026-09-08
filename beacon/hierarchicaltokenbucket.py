"""Hierarchical token buckets: per-tenant limits under a shared ceiling that can be borrowed.

A single rate limit cannot express a common need: each tenant should
get a guaranteed rate, but the whole set of tenants together must not
exceed the link's capacity, and idle tenants' unused rate should be
lendable to busy ones rather than wasted. A hierarchy of token
buckets expresses exactly that. Each child bucket has its own rate,
the tenant's guarantee, and they all sit under a parent bucket whose
rate is the shared ceiling. A request must draw a token from its
child and from the parent, so a tenant is held to its own rate by the
child and the whole system is held to the ceiling by the parent, and
because the parent is shared, a tenant that has drained its child can
still be served only if the parent has tokens the other tenants left
unspent, which is the borrowing. The result is a guarantee that
holds under contention and generosity that appears under slack. The
module refills the parent and children by elapsed time, admits a
request only when both the child and the parent have a token, and
reports which level denied a request, so the difference between hit
your own limit and the system is full is visible rather than merged
into one opaque rejection.
"""

from __future__ import annotations

from beacon.errors import Invalid


class HierarchicalTokenBucket:
    def __init__(
        self, ceiling_rate: float, child_rates: dict[str, float]
    ) -> None:
        if ceiling_rate <= 0:
            raise Invalid("the ceiling rate must be positive")
        if not child_rates:
            raise Invalid("a hierarchy needs at least one child bucket")
        self.ceiling_rate = ceiling_rate
        self.child_rates = dict(child_rates)
        self.parent_tokens = ceiling_rate
        self.child_tokens = dict(child_rates)

    def refill(self, elapsed: float) -> None:
        if elapsed < 0:
            raise Invalid("time does not run backward")
        self.parent_tokens = min(
            self.ceiling_rate,
            self.parent_tokens + self.ceiling_rate * elapsed,
        )
        for child, rate in self.child_rates.items():
            self.child_tokens[child] = min(
                rate, self.child_tokens[child] + rate * elapsed
            )

    def admit(self, child: str) -> str:
        if child not in self.child_tokens:
            raise Invalid(f"{child} is not a child bucket")
        if self.child_tokens[child] < 1:
            return "denied-by-child"
        if self.parent_tokens < 1:
            return "denied-by-ceiling"
        self.child_tokens[child] -= 1
        self.parent_tokens -= 1
        return "admitted"
