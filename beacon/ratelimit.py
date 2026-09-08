"""Response rate limiting: the amplifier turns itself down, not off.

An open resolver answering large responses to spoofed sources
is a weapon someone else aims, and response rate limiting is
the safety: per source network, count responses per window,
and past the budget stop answering normally. The subtlety that
separates RRL from a plain limiter is the slip: instead of
going silent, every Nth excess query still gets a truncated
reply, a few bytes telling a legitimate client to retry over
TCP, because the spoofed victim never retries while the real
client does, and that asymmetry is the whole filter. Going
fully silent would make the resolver useless to exactly the
victim being flooded in its name; slipping keeps the door
cracked at one part in N while the amplification factor drops
from hundreds to nearly nothing, and the ledger reports both
sides of the safety: bytes not amplified, and slips that let
real clients find their way back in.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid

WINDOW_BUDGET = 5
SLIP_RATE = 3
FULL_RESPONSE_BYTES = 4000
SLIP_BYTES = 60


@dataclass
class SourceState:
    served_in_window: int = 0
    excess: int = 0


@dataclass
class ResponseRateLimiter:
    sources: dict[str, SourceState] = field(default_factory=dict)
    bytes_not_amplified: int = 0
    slips_sent: int = 0
    answered: int = 0

    def respond(self, source_net: str) -> str:
        state = self.sources.setdefault(
            source_net, SourceState()
        )
        if state.served_in_window < WINDOW_BUDGET:
            state.served_in_window += 1
            self.answered += 1
            return f"{source_net}: full answer"
        state.excess += 1
        if state.excess % SLIP_RATE == 0:
            self.slips_sent += 1
            self.bytes_not_amplified += (
                FULL_RESPONSE_BYTES - SLIP_BYTES
            )
            return (
                f"{source_net}: SLIP, truncated retry-over-tcp "
                "hint; the spoofed victim never retries and "
                "the real client does, which is the whole "
                "filter"
            )
        self.bytes_not_amplified += FULL_RESPONSE_BYTES
        return f"{source_net}: dropped ({state.excess} excess)"

    def end_window(self) -> None:
        for state in self.sources.values():
            state.served_in_window = 0
            state.excess = 0

    def amplification_report(self, floods: int) -> str:
        if floods < 1:
            raise Invalid("a report needs a flood to report on")
        naive_bytes = floods * FULL_RESPONSE_BYTES
        sent = naive_bytes - self.bytes_not_amplified
        factor_before = FULL_RESPONSE_BYTES // SLIP_BYTES
        return (
            f"{floods} flood response(s) would have shipped "
            f"{naive_bytes} bytes; {sent} actually left, "
            f"{self.slips_sent} slip(s) kept the door cracked, "
            f"and the amplification factor fell from about "
            f"{factor_before}x toward one"
        )
