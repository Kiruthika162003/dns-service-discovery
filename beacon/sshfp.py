"""SSHFP records: verify an SSH host key from DNSSEC-signed DNS instead of trusting it blindly.

The first time an SSH client connects to a host it has never seen,
it is shown the host's key fingerprint and asked to trust it, and
almost everyone types yes without checking, which means the first
connection is wide open to a machine-in-the-middle that offers its
own key. SSHFP closes that window by publishing the host key's
fingerprint in DNS, secured by DNSSEC, so the client can verify the
key it is offered against an authenticated record rather than
trusting it on faith. The record names the key algorithm and the
fingerprint type, and the client, having fetched the SSHFP records
for the host, accepts the presented key only if its fingerprint
matches a record for the same algorithm. Two conditions make the
protection real, and the module keeps them in view: the fingerprint
type must be the stronger SHA-256 rather than the weak SHA-1, since a
fingerprint an attacker can forge protects nothing, and the DNS
answer must be DNSSEC-validated, since an unsigned SSHFP an attacker
can spoof is no better than trust-on-first-use. The module verifies
a presented key against the records and reports whether a record's
fingerprint type is strong enough to rely on.
"""

from __future__ import annotations

from beacon.errors import Invalid

FP_TYPES = {1: "SHA-1", 2: "SHA-256"}


def verify(
    records: list[tuple[int, int, str]],
    key_algorithm: int,
    presented_fingerprint: str,
    fp_type: int = 2,
) -> bool:
    if fp_type not in FP_TYPES:
        raise Invalid(
            f"fingerprint type {fp_type} is not one SSHFP defines"
        )
    for algorithm, record_fp_type, fingerprint in records:
        if (
            algorithm == key_algorithm
            and record_fp_type == fp_type
            and fingerprint == presented_fingerprint
        ):
            return True
    return False


def strong_enough(fp_type: int) -> bool:
    if fp_type not in FP_TYPES:
        raise Invalid(f"fingerprint type {fp_type} is not one SSHFP defines")
    return fp_type == 2
