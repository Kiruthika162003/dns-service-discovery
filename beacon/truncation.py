"""Truncation: the datagram is small, the answer is not, and the flag says retry.

UDP answers fit in a modest datagram, and answers with many
records do not fit, so the protocol carries a truncation flag:
the server sends what fits, marks the message truncated, and
the client retries the same question over TCP where size is
not the constraint. The economics matter because TCP costs a
handshake: a fleet whose answers routinely truncate pays the
handshake tax on most queries, which is a zone-shape complaint
wearing a transport problem's clothes, and the report says so
when the truncation rate crosses the line. The rule this
module refuses to bend is silent truncation: dropping records
to fit without setting the flag hands the client a subset it
believes is complete, and a load balancer that saw three of
twelve backends is not degraded, it is confidently wrong,
which is the worst state a distributed system offers.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid

UDP_LIMIT_BYTES = 512
RECORD_BYTES = 80
TCP_HANDSHAKE_TAX = 2


@dataclass
class TransportLedger:
    udp_answers: int = 0
    truncated: int = 0
    tcp_retries: int = 0
    handshake_ticks: int = 0

    def answer(
        self, record_count: int, client_retries: bool = True
    ) -> str:
        if record_count < 1:
            raise Invalid("an answer needs records")
        size = record_count * RECORD_BYTES
        if size <= UDP_LIMIT_BYTES:
            self.udp_answers += 1
            return (
                f"{record_count} record(s), {size} bytes: fits "
                "the datagram"
            )
        fits = UDP_LIMIT_BYTES // RECORD_BYTES
        self.truncated += 1
        if not client_retries:
            return (
                f"{record_count} record(s): sent {fits} with "
                "the truncation flag SET; the client declined "
                "to retry and knows it holds a subset, which "
                "is degraded, not wrong"
            )
        self.tcp_retries += 1
        self.handshake_ticks += TCP_HANDSHAKE_TAX
        return (
            f"{record_count} record(s): truncated at {fits}, "
            f"client retried over tcp, handshake tax "
            f"{TCP_HANDSHAKE_TAX} tick(s), full answer "
            "delivered"
        )

    def silent_truncation(self, record_count: int) -> str:
        raise Invalid(
            f"refusing to drop records from a {record_count} "
            "record answer without the flag: a client holding "
            "three of twelve backends unmarked is not "
            "degraded, it is confidently wrong, the worst "
            "state a distributed system offers"
        )

    def shape_report(self) -> str:
        total = self.udp_answers + self.truncated
        if total == 0:
            raise Invalid("no answers to report on")
        rate = 100 * self.truncated // total
        line = (
            f"{total} answer(s): {self.truncated} truncated "
            f"({rate}%), {self.tcp_retries} tcp retry(ies), "
            f"{self.handshake_ticks} handshake tick(s) paid"
        )
        if rate > 30:
            line += (
                "; a fleet that truncates this often has a "
                "zone-shape complaint wearing a transport "
                "problem's clothes"
            )
        return line
