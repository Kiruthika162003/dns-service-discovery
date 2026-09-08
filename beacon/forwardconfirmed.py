"""Forward-confirmed reverse DNS: the loose handshake where a name and address agree.

Mail servers and log analyzers often want to check that a connecting
address is not casually spoofing its identity, and forward-confirmed
reverse DNS is the cheap test they use. Starting from the address, it
looks up the reverse PTR record to get a name, then looks up that
name's forward address records, and it is confirmed only if the
original address appears among them. The round trip proves a loose
but useful thing: whoever controls the reverse zone for the address
and whoever controls the forward zone for the name have been set to
agree with each other, which a random spoofer of one but not the
other cannot fake. The module is careful to state what this does and
does not prove. It is not cryptographic authentication, since an
attacker who controls both the forward and reverse records for their
own address and name passes it trivially, so FCrDNS filters casual
mismatch and misconfiguration, not a determined adversary. A missing
PTR, or a name whose forward records omit the address, both fail the
check, and for different reasons the module distinguishes. It looks up
the PTR, resolves the name forward, and confirms the address is
present, refusing the check when there is no PTR to start from.
"""

from __future__ import annotations

from beacon.errors import Invalid


def confirmed(
    address: str,
    ptr: dict[str, str],
    forward: dict[str, list[str]],
) -> bool:
    name = ptr.get(address)
    if name is None:
        raise Invalid(
            f"{address} has no PTR record; there is no name to "
            "confirm against, so the check cannot even begin"
        )
    addresses = forward.get(name, [])
    return address in addresses


def failure_reason(
    address: str,
    ptr: dict[str, str],
    forward: dict[str, list[str]],
) -> str:
    name = ptr.get(address)
    if name is None:
        return "no-ptr"
    if address not in forward.get(name, []):
        return "forward-mismatch"
    return "confirmed"
