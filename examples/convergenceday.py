"""The convergence day: replicas drift, then reconcile without a coordinator in sight.

Run with: python -m examples.convergenceday
"""

from __future__ import annotations

from beacon.merkletree import MerkleTree, divergent_keys
from beacon.orset import ORSet
from beacon.pncounter import PNCounter
from beacon.readrepair import resolve
from beacon.scuttlebutt import deltas_for_peer
from beacon.versionvector import compare, merge


def morning_the_conflict():
    edit_a = {"a": 2, "b": 1}
    edit_b = {"a": 1, "b": 2}
    print(f"morning  version vectors say: {compare(edit_a, edit_b)}")
    settled = merge(edit_a, edit_b)
    print(f"         merge settles to {settled}")


def midday_the_counter():
    left = PNCounter()
    left.increment("a", 10)
    left.decrement("a", 3)
    right = PNCounter()
    right.increment("b", 5)
    total = left.merge(right).value()
    print(f"midday   PN-counter converges to {total} either merge order")


def afternoon_the_set():
    left = ORSet()
    left.add("web", "t1")
    right = left.merge(ORSet())
    right.remove("web")
    left.add("web", "t2")
    print(f"afternoon add-wins over concurrent remove = {left.merge(right).contains('web')}")


def evening_the_merkle():
    base = {f"k{i:03d}": f"v{i}" for i in range(256)}
    other = dict(base)
    other["k100"] = "changed"
    found, comparisons = divergent_keys(MerkleTree(base), MerkleTree(other))
    print(f"evening  merkle found {found} in {comparisons} comparisons of 256")


def night_the_read_repair():
    responses = {"r1": ("old", 3), "r2": ("new", 5), "r3": ("old", 3)}
    value, version, stale = resolve(responses)
    print(f"night    read repair keeps {value} v{version}, repairs {stale}")


def dawn_the_gossip():
    mine = {"n1": ("up", 5), "n2": ("down", 3)}
    peer_digest = {"n1": 5, "n2": 1}
    deltas = deltas_for_peer(mine, peer_digest)
    print(f"dawn     scuttlebutt sends only the deltas the peer lacks: {sorted(deltas)}")


def main() -> int:
    morning_the_conflict()
    midday_the_counter()
    afternoon_the_set()
    evening_the_merkle()
    night_the_read_repair()
    dawn_the_gossip()
    try:
        resolve({})
    except Exception as refusal:
        print(f"honest:  {str(refusal).split(';')[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
