"""AXFR consistency: one snapshot, bracketed by a serial that must match end to end.

A full zone transfer ships every record of a zone, and the copy the
secondary ends up with must represent the zone at a single instant,
not a smear across edits that happened while the bytes were in
flight. The protocol enforces the snapshot with a bracket: an AXFR
begins with the zone's SOA record and ends with the SOA record
again, and the serial number in the closing SOA must equal the one
in the opening SOA. If the zone was edited mid-transfer its serial
would advance, the closing SOA would carry a different number than
the opening one, and the secondary would know its copy straddles two
versions and must be discarded rather than served, because a zone
that is half the old version and half the new is a state that never
actually existed. The SOA-first, SOA-last framing also lets the
receiver know where the stream begins and ends without a separate
length. The module validates that a transfer opens and closes on the
SOA and that the two serials agree, refusing a transfer whose serial
moved as the inconsistent snapshot it is.
"""

from __future__ import annotations

from beacon.errors import Invalid


def validate_axfr(
    records: list[tuple[str, int | None]],
) -> str:
    if len(records) < 2:
        raise Invalid(
            "an AXFR needs at least an opening and closing SOA; a "
            "shorter stream is not a framed transfer"
        )
    first_type, first_serial = records[0]
    last_type, last_serial = records[-1]
    if first_type != "SOA" or last_type != "SOA":
        raise Invalid(
            "an AXFR must open and close on the SOA; without the "
            "bracket the receiver cannot tell where the snapshot "
            "begins and ends"
        )
    if first_serial != last_serial:
        raise Invalid(
            f"the zone changed mid-transfer, serial {first_serial} "
            f"to {last_serial}; the copy straddles two versions and "
            "must be discarded, not served"
        )
    return "consistent snapshot"
