"""Chain replication: writes enter at the head, commit at the tail, reads come from the tail.

Chain replication arranges the replicas in a line, a head, a
sequence of middles, and a tail, and routes operations to give
strong consistency with a pleasingly simple failure story. A write
enters at the head and propagates down the chain node by node, and it
is committed only when it reaches the tail, so the tail has seen
every committed write and nothing uncommitted. Reads are served by
the tail alone, which means a read always reflects exactly the
committed state, no quorum and no version reconciliation, because the
one node that answers reads is the one node guaranteed current. The
load splits naturally, writes stress the head and the propagation
path while reads stress the tail, so the two do not contend. Recovery
is unusually clean: a failed middle node is spliced out by connecting
its neighbors, a failed head promotes the next node, and a failed
tail promotes its predecessor, each a local repair rather than a
cluster-wide election. The cost the module keeps in view is write
latency, since a write must traverse the entire chain before it
commits, so a longer chain is more durable and more latent at once.
The module gives the write path, names the read node, and reconnects
the chain around a failure.
"""

from __future__ import annotations

from beacon.errors import Invalid


class Chain:
    def __init__(self, nodes: list[str]) -> None:
        if not nodes:
            raise Invalid("a chain needs at least one node")
        self.nodes = list(nodes)

    def head(self) -> str:
        return self.nodes[0]

    def tail(self) -> str:
        return self.nodes[-1]

    def write_path(self) -> list[str]:
        return list(self.nodes)

    def read_node(self) -> str:
        return self.tail()

    def committed(self, reached: str) -> bool:
        return reached == self.tail()

    def remove(self, failed: str) -> None:
        if failed not in self.nodes:
            raise Invalid(f"{failed} is not in the chain")
        if len(self.nodes) == 1:
            raise Invalid(
                "removing the only node leaves no chain to splice; "
                "that is an outage, not a repair"
            )
        self.nodes.remove(failed)

    def write_latency(self, per_hop: int) -> int:
        return per_hop * len(self.nodes)
