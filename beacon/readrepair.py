"""Read repair: heal the replicas that answered a read with stale data, on the way past.

A quorum read collects a value from several replicas, and because
replication is asynchronous some of them may still hold an older
version, so the coordinator must pick the newest, by version, and
return it. Read repair takes the opportunity that the read already
created: having seen which replicas were behind, it writes the
winning value back to them, so the divergence a read exposed is
healed as a side effect of serving the read rather than left for a
background sweep. The property worth stating is that read repair is
opportunistic, not complete. It fixes exactly the data that gets
read, so hot keys stay converged almost for free while cold keys
that no one reads can stay divergent indefinitely, which is why a
system still needs periodic anti-entropy underneath it, to reach
the data read repair never visits. The module selects the newest
version among the responses, names the replicas whose version
trails it as the ones to repair, and refuses a read with no
responses, since a repair needs at least one replica's answer to
know what the newest version even is.
"""

from __future__ import annotations

from beacon.errors import Invalid


def resolve(
    responses: dict[str, tuple[str, int]],
) -> tuple[str, int, list[str]]:
    if not responses:
        raise Invalid(
            "a read with no responses has no newest version to "
            "repair toward; a quorum needs at least one answer"
        )
    newest_value, newest_version = max(
        responses.values(), key=lambda pair: pair[1]
    )
    stale = sorted(
        replica
        for replica, (_, version) in responses.items()
        if version < newest_version
    )
    return newest_value, newest_version, stale


def is_converged(responses: dict[str, tuple[str, int]]) -> bool:
    _, _, stale = resolve(responses)
    return not stale
