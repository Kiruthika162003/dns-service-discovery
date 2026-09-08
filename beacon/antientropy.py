"""Anti-entropy: gossip spreads the news, the full sync corrects the record.

Rumor is fast and lossy: a dropped packet here, a restarted
node there, and two members quietly hold different catalogs
for weeks, each certain. Anti-entropy is the slow corrective
running behind the fast gossip: periodically, two members
compare digests of their full state, and only when the digests
differ do they exchange keys to find the drift, which keeps
the common case, agreement, at the cost of one hash compare.
Repair is by version, never by majority: the higher version
wins each drifted key regardless of which member holds it,
because freshness is evidence and popularity is not. The
drift report is the operational payoff, naming what diverged
and for roughly how long it could have been wrong, since
"the members disagreed about billing/b3" matters less than
knowing the disagreement could be three weeks old, which is
the age of the trust problem, not the data problem.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from beacon.errors import Invalid


@dataclass
class MemberCatalog:
    name: str
    state: dict[str, tuple[str, int]] = field(
        default_factory=dict
    )

    def put(self, key: str, value: str, version: int) -> None:
        held = self.state.get(key)
        if held is not None and held[1] >= version:
            raise Invalid(
                f"{key}: version {version} does not beat "
                f"{held[1]}; time does not run backward here"
            )
        self.state[key] = (value, version)

    def digest(self) -> str:
        parts = [
            f"{key}={value}@{version}"
            for key, (value, version) in sorted(
                self.state.items()
            )
        ]
        return hashlib.sha256(
            "|".join(parts).encode()
        ).hexdigest()[:12]


def sync_round(
    left: MemberCatalog, right: MemberCatalog, now: int
) -> str:
    if left.digest() == right.digest():
        return (
            f"{left.name} and {right.name} agree; one hash "
            "compare, no keys exchanged, which is the common "
            "case doing its job"
        )
    drifted = []
    keys = set(left.state) | set(right.state)
    for key in sorted(keys):
        held_left = left.state.get(key)
        held_right = right.state.get(key)
        if held_left == held_right:
            continue
        left_version = held_left[1] if held_left else -1
        right_version = held_right[1] if held_right else -1
        if left_version > right_version:
            right.state[key] = held_left
            winner, loser = left.name, right.name
            age = now - right_version if right_version >= 0 else now
        else:
            left.state[key] = held_right
            winner, loser = right.name, left.name
            age = now - left_version if left_version >= 0 else now
        drifted.append(
            f"{key}: {winner}'s version wins, {loser} could "
            f"have been wrong for up to {age} tick(s)"
        )
    lines = [
        f"{len(drifted)} drifted key(s) repaired by version, "
        "never by majority; freshness is evidence and "
        "popularity is not"
    ]
    lines.extend(f"  {entry}" for entry in drifted)
    return "\n".join(lines)
