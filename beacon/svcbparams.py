"""SVCB parameters: the mandatory key that tells a client which others it may not ignore.

An SVCB or HTTPS record carries a set of service parameters, ALPN
protocols, an alternate port, address hints, and a client is free
to skip parameters it does not understand, which is what lets new
parameters be deployed without breaking old clients. That freedom
would be dangerous for a parameter whose omission changes the
meaning of the record, so RFC 9460 adds the mandatory parameter,
key zero, which lists the other keys a client must understand for
the record to be safe to use. A client that does not understand
every key named in mandatory must ignore the whole record rather
than act on a partial reading of it. The mandatory list itself has
rules that keep it coherent, and the module enforces them: it may
not list key zero, since a record cannot require understanding of
the requirement itself, it may not name a key that is not actually
present in the record, since requiring an absent parameter is a
contradiction, and it may not repeat a key. With the list
validated, the module decides whether a given client, with its set
of understood keys, must ignore the record, which is the whole
purpose the mandatory key exists to serve.
"""

from __future__ import annotations

from beacon.errors import Invalid

MANDATORY_KEY = 0


def validate_mandatory(
    present_keys: set[int], mandatory: list[int]
) -> None:
    if MANDATORY_KEY in mandatory:
        raise Invalid(
            "the mandatory list names key 0, itself; a record "
            "cannot require understanding of the requirement"
        )
    if len(mandatory) != len(set(mandatory)):
        raise Invalid(
            "the mandatory list repeats a key; each requirement is "
            "stated once"
        )
    for key in mandatory:
        if key not in present_keys:
            raise Invalid(
                f"mandatory names key {key}, which is not present "
                "in the record; requiring an absent parameter is a "
                "contradiction"
            )


def client_must_ignore(
    mandatory: set[int], understood: set[int]
) -> bool:
    return not mandatory <= understood
