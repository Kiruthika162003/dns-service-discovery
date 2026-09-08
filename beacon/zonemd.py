"""ZONEMD: a digest of the whole zone, so a consumer can verify the file arrived intact.

DNSSEC signs individual records so a resolver can trust an answer,
but it does not tell a consumer of an entire zone, someone who
downloaded the root zone to serve locally, or received a zone by
transfer, that the file they hold is complete and unaltered as a
whole. A record could be missing, or the file truncated, and every
remaining signature would still verify. ZONEMD, RFC 8976, adds a
message digest of the entire zone as a record in the zone itself, so
a consumer recomputes the digest over all the records and compares
it to the ZONEMD value, catching any corruption, truncation, or
tampering of the file at rest or in transit. It complements DNSSEC
rather than replacing it: DNSSEC protects each response, ZONEMD
protects the collection, and a zone can be both signed and digested
so a locally served copy is verified as a whole before it is trusted
to answer from. The module computes a digest over the canonically
sorted records, verifies a zone against a stored digest, and refuses
to verify an empty zone, whose digest would certify nothing.
"""

from __future__ import annotations

import hashlib

from beacon.errors import Invalid


def compute_digest(records: list[str]) -> str:
    if not records:
        raise Invalid(
            "an empty zone has nothing to digest; a ZONEMD over no "
            "records would certify emptiness, not integrity"
        )
    canonical = "\n".join(sorted(records))
    return hashlib.sha256(canonical.encode()).hexdigest()


def verify(records: list[str], stored_digest: str) -> bool:
    return compute_digest(records) == stored_digest


def detects_missing_record(
    full: list[str], truncated: list[str]
) -> bool:
    return compute_digest(full) != compute_digest(truncated)
