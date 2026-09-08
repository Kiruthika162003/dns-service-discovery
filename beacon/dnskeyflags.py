"""DNSKEY flags: the ZONE bit that lets a key sign, and the SEP bit that is only a hint.

A DNSKEY record carries a flags field, and three bits in it matter.
The ZONE bit must be set for a key to be allowed to sign zone data at
all, so a DNSKEY without it is not a zone key and a validator must
not accept signatures from it, no matter how the key otherwise looks.
The REVOKE bit marks a key its owner has retired, and a revoked key
must not be used even though it is still published, which is how a
key is withdrawn without a validator ever missing the withdrawal. The
SEP bit, secure entry point, is the subtle one and the module makes
its limit explicit: it is conventionally set on the key-signing key,
the one the parent's DS record points at, but it is only a hint. It
does not change what the key can cryptographically do, and the actual
trust anchor is established by the DS chain, not by a bit a zone can
set on any key it likes. A validator that decided which key to trust
by the SEP bit rather than by following the DS could be steered
wrong, so SEP guides key management, it does not confer trust. The
module classifies a key from its flags, refuses to treat a non-zone
key as signing-capable, and reports SEP as the advisory marker it is.
"""

from __future__ import annotations

from beacon.errors import Invalid

ZONE = 0x0100
REVOKE = 0x0080
SEP = 0x0001


def is_zone_key(flags: int) -> bool:
    return bool(flags & ZONE)


def is_revoked(flags: int) -> bool:
    return bool(flags & REVOKE)


def is_sep(flags: int) -> bool:
    return bool(flags & SEP)


def may_sign(flags: int) -> bool:
    if not is_zone_key(flags):
        raise Invalid(
            "the ZONE bit is not set, so this DNSKEY may not sign "
            "zone data; a validator must reject its signatures"
        )
    return not is_revoked(flags)
