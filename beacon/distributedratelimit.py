"""Distributed rate limiting: local buckets that spend fast, reconciled to a global budget.

A rate limit meant to hold across a fleet of servers cannot be
enforced by asking a central authority on every request, that
round trip would cost more than the work it guards, so the practical
design splits a global budget into local allowances and reconciles
periodically. Each server is handed a slice of the global rate to
spend locally without coordination, which keeps the hot path free of
network calls, and on a slower cycle the servers report what they
spent and the remaining global budget is redistributed. The tension
this creates is the honest cost: between reconciliations a server can
only see its own local slice, so a fleet can briefly overspend the
global limit if traffic clumps onto servers whose neighbors sat
idle, and it can briefly underspend if a busy server exhausts its
slice while idle peers hold unused allowance the busy one cannot yet
borrow. Tighter reconciliation shrinks both errors at the cost of
more coordination, which is the dial. The module hands out local
allowances from a global budget, spends against a local slice
without coordination, and reconciles by pooling the unspent
remainder and reallocating it, so the approximation and its bound are
explicit.
"""

from __future__ import annotations

from beacon.errors import Invalid, Refused


class DistributedRateLimiter:
    def __init__(self, global_budget: int, servers: list[str]) -> None:
        if global_budget < 1:
            raise Invalid("a global budget below one admits nothing")
        if not servers:
            raise Invalid("no servers to distribute the budget across")
        self.global_budget = global_budget
        self.servers = list(servers)
        self.local = {
            server: global_budget // len(servers) for server in servers
        }

    def spend(self, server: str) -> None:
        if server not in self.local:
            raise Invalid(f"{server} holds no local allowance")
        if self.local[server] < 1:
            raise Refused(
                f"{server} has spent its local slice; the fleet may "
                "have budget elsewhere, but borrowing waits for the "
                "next reconcile"
            )
        self.local[server] -= 1

    def remaining_local(self, server: str) -> int:
        return self.local.get(server, 0)

    def reconcile(self) -> None:
        pooled = sum(self.local.values())
        share = pooled // len(self.servers)
        remainder = pooled - share * len(self.servers)
        for index, server in enumerate(self.servers):
            self.local[server] = share + (1 if index < remainder else 0)
