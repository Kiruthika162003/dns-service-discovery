"""Deficit round robin: fair scheduling by bytes, not by turns, when packets differ in size.

Plain round robin gives every queue an equal number of turns, which
is only fair if every turn costs the same, and it does not when
queues hold packets of wildly different sizes: a queue of tiny
packets and a queue of jumbo ones each get one turn, but the jumbo
queue moves far more bytes, so byte-rate fairness is broken. Deficit
round robin fixes it by scheduling in bytes. Each queue is given a
quantum of bytes per round and carries a deficit counter that
accumulates unused allowance, and a packet is sent only when the
deficit counter has grown to at least the packet's size, at which
point the size is subtracted. A queue whose packet is too big this
round banks the quantum as deficit and sends next round when the
deficit has grown enough, so over rounds every queue gets bandwidth
in proportion to its quantum regardless of packet size, and no queue
starves. The quantum tunes the tradeoff between fairness granularity
and per-round work. The module runs a round over the queues,
advancing each deficit by the quantum and dequeuing whatever now
fits, and reports the bytes each queue sent so the byte-fairness is
observable rather than assumed.
"""

from __future__ import annotations

from beacon.errors import Invalid


class DeficitRoundRobin:
    def __init__(self, quantum: int) -> None:
        if quantum < 1:
            raise Invalid(
                "a quantum of zero bytes never lets a packet through; "
                "no queue would ever send"
            )
        self.quantum = quantum
        self.deficit: dict[str, int] = {}

    def run_round(
        self, queues: dict[str, list[int]]
    ) -> dict[str, list[int]]:
        sent: dict[str, list[int]] = {}
        for queue, packets in queues.items():
            balance = self.deficit.get(queue, 0) + self.quantum
            emitted = []
            while packets and packets[0] <= balance:
                size = packets.pop(0)
                balance -= size
                emitted.append(size)
            self.deficit[queue] = balance if packets else 0
            sent[queue] = emitted
        return sent

    def bytes_sent(self, sent: dict[str, list[int]]) -> dict[str, int]:
        return {queue: sum(sizes) for queue, sizes in sent.items()}
