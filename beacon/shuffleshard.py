"""Shuffle sharding: two tenants share a whole shard almost never.

Plain sharding assigns each tenant to one shard of workers,
and a poison tenant takes its whole shard's tenants down with
it. Shuffle sharding deals each tenant a personal hand of
workers drawn from the full deck, and the arithmetic is the
product's soul: with eight workers choose two per tenant,
there are twenty-eight possible hands, so two tenants share
BOTH workers only when they drew the same hand, and a poison
tenant that kills its two workers leaves every other tenant
with at least one live worker in almost every case. The blast
report measures instead of promising: for a poisoned tenant it
counts how many other tenants lost all, some, or none of their
hand, and the fully-shared count is the number the whole
technique exists to shrink, printed beside the plain-sharding
equivalent where every co-tenant of the shard loses
everything.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from beacon.errors import Invalid


def _deal(
    workers: tuple[str, ...], tenant: str, hand_size: int
) -> tuple[str, ...]:
    shuffled = sorted(
        workers,
        key=lambda name: hashlib.sha256(
            f"{tenant}|{name}".encode()
        ).hexdigest(),
    )
    return tuple(sorted(shuffled[:hand_size]))


@dataclass(frozen=True)
class ShuffleShard:
    workers: tuple[str, ...]
    hand_size: int

    def __post_init__(self) -> None:
        if self.hand_size < 1:
            raise Invalid("a hand of zero cards plays nothing")
        if self.hand_size >= len(self.workers):
            raise Invalid(
                "a hand the size of the deck is plain "
                "sharding with extra steps"
            )

    def hand_for(self, tenant: str) -> tuple[str, ...]:
        return _deal(self.workers, tenant, self.hand_size)

    def blast_report(
        self, poisoned_tenant: str, tenants: list[str]
    ) -> str:
        if poisoned_tenant not in tenants:
            raise Invalid(
                "the poisoned tenant must be in the population"
            )
        dead_workers = set(self.hand_for(poisoned_tenant))
        lost_all = []
        lost_some = 0
        lost_none = 0
        for tenant in tenants:
            if tenant == poisoned_tenant:
                continue
            hand = set(self.hand_for(tenant))
            overlap = len(hand & dead_workers)
            if overlap == len(hand):
                lost_all.append(tenant)
            elif overlap:
                lost_some += 1
            else:
                lost_none += 1
        others = len(tenants) - 1
        plain_blast = others // (
            len(self.workers) // self.hand_size
        )
        lines = [
            f"poison kills {sorted(dead_workers)}: of "
            f"{others} other tenant(s), {len(lost_all)} lost "
            f"everything, {lost_some} lost part of a hand, "
            f"{lost_none} untouched"
        ]
        if lost_all:
            lines.append(
                f"  fully shared hands: {', '.join(lost_all)}"
            )
        lines.append(
            f"  plain sharding would take roughly "
            f"{plain_blast} co-tenant(s) down whole; the "
            "fully-shared count is the number this technique "
            "exists to shrink"
        )
        return "\n".join(lines)
