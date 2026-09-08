"""DANE TLSA: pin a service's certificate in DNS so a forged cert from any CA is rejected.

The web's certificate trust rests on a large set of certificate
authorities, any of which can issue a certificate for any name, so a
single compromised or coerced CA can mint a valid-looking
certificate for a domain it has no business certifying. DANE moves
the trust anchor into the domain's own DNS. A TLSA record, secured
by DNSSEC, pins what the domain's certificate must be, and the
client checks the certificate a server presents against it. The
record's usage field decides how strict the pin is: the DANE-EE
usage says the presented certificate must match this record and the
CA chain is irrelevant, so even a perfectly valid certificate from a
trusted CA is rejected if it is not the pinned one, which is exactly
what stops a mis-issued certificate. The selector and matching
fields say what is compared, the whole certificate or just its
public key, exactly or by a hash. The trade is that DANE relocates
trust from the CA system to DNSSEC, so it is only as sound as the
domain's DNSSEC, a compromise of which becomes a certificate
compromise. The module decides whether a presented digest matches a
TLSA record and whether the usage bypasses CA validation.
"""

from __future__ import annotations

from beacon.errors import Invalid

USAGES = {0: "PKIX-TA", 1: "PKIX-EE", 2: "DANE-TA", 3: "DANE-EE"}


def matches(
    tlsa_digest: str, presented_digest: str, usage: int
) -> bool:
    if usage not in USAGES:
        raise Invalid(
            f"usage {usage} is not a TLSA certificate usage; it "
            f"knows {sorted(USAGES)}"
        )
    return tlsa_digest == presented_digest


def bypasses_ca(usage: int) -> bool:
    if usage not in USAGES:
        raise Invalid(f"usage {usage} is not a TLSA certificate usage")
    return usage in (2, 3)


def rejects_misissued(usage: int, presented_is_pinned: bool) -> bool:
    return bypasses_ca(usage) and not presented_is_pinned
