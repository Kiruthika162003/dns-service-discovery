"""Query classes: answer your zone's class, treat ANY as a meta-query, refuse the rest.

Beside the record type, a DNS query carries a class, and though
the internet class IN is the only one almost anyone uses, the
field is real and a server has to handle it correctly. The chaos
class CH carries the server-description names, and the hesiod class
HS is a historical directory service, so a server authoritative for
an IN zone answers IN queries and must not answer a CH or HS query
against that zone as if the class did not matter, because the class
is part of the name's identity and a record in one class says
nothing about another. The class ANY, value 255, is not a real
class a zone lives in but a meta-query asking across classes, and
it is handled as the special case it is rather than matched against
the zone's class. The module maps the known class mnemonics to
their numbers, answers a query whose class matches the zone, treats
ANY as the cross-class meta-query, and refuses a query whose class
neither matches the zone nor is ANY, since answering an IN zone to
a HS query would be inventing an authority the server does not have.
"""

from __future__ import annotations

from beacon.errors import Invalid, Refused

CLASSES = {"IN": 1, "CH": 3, "HS": 4, "ANY": 255}


def handle(qclass: str, zone_class: str) -> str:
    if qclass not in CLASSES:
        raise Invalid(
            f"{qclass!r} is not a known query class; the server "
            f"knows {', '.join(CLASSES)}"
        )
    if qclass == "ANY":
        return "meta-query across classes"
    if qclass != zone_class:
        raise Refused(
            f"this server is authoritative for the {zone_class} "
            f"class, not {qclass}; a record in one class says "
            "nothing about another, so answering would invent an "
            "authority the server does not have"
        )
    return "answer"


def code_of(qclass: str) -> int:
    if qclass not in CLASSES:
        raise Invalid(f"{qclass!r} has no assigned class number")
    return CLASSES[qclass]
