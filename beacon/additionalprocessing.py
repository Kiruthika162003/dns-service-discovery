"""Additional-section glue: a saved round trip, but only for names you can vouch for.

When a server answers with a record whose data points at another
host, an MX naming a mail server, an SRV or NS naming a target, the
client's very next question is predictable: what is that host's
address. Additional-section processing answers it in advance,
attaching the target's A and AAAA records to the same response so
the client is spared a second query. The saving is real and the
danger is specific. The server may only vouch for addresses inside
its own zones, so it attaches glue only for in-bailiwick targets;
an address record for an out-of-zone name would be unauthenticated
data the server has no authority over, and attaching it is a
classic cache-poisoning vector, a way to smuggle a forged address
for some unrelated name into the client's cache under cover of a
legitimate answer. So the module collects additional records for
the answer's targets, includes them only when the target lies
within the served zone and an address is actually held, and drops
out-of-zone targets rather than vouching for addresses it cannot
stand behind.
"""

from __future__ import annotations


def _in_zone(name: str, apex: str) -> bool:
    name = name.rstrip(".")
    apex = apex.rstrip(".")
    return name == apex or name.endswith("." + apex)


def additional_for(
    targets: list[str],
    addresses: dict[str, list[str]],
    apex: str,
) -> dict[str, list[str]]:
    glue = {}
    for target in targets:
        if _in_zone(target, apex) and target in addresses:
            glue[target] = list(addresses[target])
    return glue


def dropped_targets(targets: list[str], apex: str) -> list[str]:
    return sorted(
        target for target in targets if not _in_zone(target, apex)
    )
