"""DNSKEY key tags: a fast checksum to narrow which key signed, but a hint, not an identity.

A signed RRset names, in its RRSIG, the key tag of the DNSKEY that
signed it, a sixteen-bit checksum over the key's bytes, so a
validator holding several keys can quickly pick out the few whose
tag matches instead of trying every key against every signature. The
tag is computed by summing the key's octets as sixteen-bit words and
folding the carry back in, the arithmetic in RFC 4034, cheap enough
to run on every key. The critical property, the one a validator must
not forget, is that the key tag is not unique: it is a checksum, not
an identifier, and two different keys can collide to the same tag,
especially within a zone that rolls keys of the same algorithm. So
the tag narrows the candidates but does not name the key, and a
validator that treated a tag match as proof it had the right key
could pick a colliding wrong one and wrongly fail a signature that a
sibling key would have verified. The correct use is to try every key
whose tag and algorithm match, not just the first. The module
computes the key tag from the key's RDATA and makes plain, by
detecting a collision between two keys, that the tag is a filter and
not a fingerprint.
"""

from __future__ import annotations

from beacon.errors import Invalid


def key_tag(rdata: bytes) -> int:
    if not rdata:
        raise Invalid("a DNSKEY with empty RDATA has no key to tag")
    accumulator = 0
    for index, octet in enumerate(rdata):
        accumulator += octet << 8 if index % 2 == 0 else octet
    accumulator += (accumulator >> 16) & 0xFFFF
    return accumulator & 0xFFFF


def tags_collide(rdata_a: bytes, rdata_b: bytes) -> bool:
    return rdata_a != rdata_b and key_tag(rdata_a) == key_tag(rdata_b)
