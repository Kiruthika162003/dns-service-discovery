"""TSIG: a shared secret and a tight clock, so a replayed message is a stale one.

Zone transfers and dynamic updates must be authenticated, and
TSIG signs each message with a secret shared between two named
peers, but a signature alone does not stop replay: an attacker
who captured a signed update could resend it unchanged and it
would still verify. TSIG binds the signature to a timestamp and
a fudge window, a few seconds of tolerance for honest clock
skew, and the receiver refuses any message whose time falls
outside now plus or minus the fudge, so a captured message is
valid only for the width of the window and a replay arriving
later is rejected as stale rather than accepted as genuine. The
window is a real trade, too tight and honest peers with drifting
clocks are locked out, too wide and the replay opportunity
grows, and the module refuses a fudge of zero because a window
of zero rejects every real message the instant either clock
disagrees by a microsecond, which is always.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Refused


@dataclass(frozen=True)
class TsigKey:
    name: str
    secret: str
    fudge: int = 5

    def __post_init__(self) -> None:
        if self.fudge <= 0:
            raise Refused(
                "a fudge of zero rejects every real message the "
                "instant either clock disagrees; give the window "
                "a few seconds of honest skew"
            )

    def verify(
        self,
        claimed_key: str,
        signed_time: int,
        now: int,
        mac_matches: bool = True,
    ) -> str:
        if claimed_key != self.name:
            raise Refused(
                f"BADKEY: message signed by {claimed_key!r} but "
                f"this peer shares a secret only with {self.name!r}"
            )
        if not mac_matches:
            raise Refused(
                "BADSIG: the MAC does not verify under the "
                "shared secret; the message was altered or the "
                "secret is wrong"
            )
        skew = abs(now - signed_time)
        if skew > self.fudge:
            raise Refused(
                f"BADTIME: message time is {skew}s from now, "
                f"outside the {self.fudge}s fudge; a replay is "
                "only valid for the width of the window"
            )
        return "verified"

    def would_accept(
        self, signed_time: int, now: int
    ) -> bool:
        return abs(now - signed_time) <= self.fudge
