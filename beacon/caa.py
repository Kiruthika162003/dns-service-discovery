"""CAA records: the zone names which CAs may issue for it, checked before issuance.

A CAA record lets a domain owner state, in DNS, which certificate
authorities are permitted to issue certificates for the domain, and
a conforming CA is required to read it and refuse to issue if it is
not on the list. The default is permissive and worth stating,
because it explains why CAA matters: a domain with no CAA record at
all places no restriction, so any CA may issue, which is exactly the
open situation CAA exists to let an owner close. When CAA records
are present, an issue property names a permitted CA, an issuewild
property does the same specifically for wildcard certificates, and
the special empty value, issue with a semicolon and no authority,
forbids all issuance. A CA about to issue checks the relevant set,
the issuewild set for a wildcard if any issuewild records exist,
otherwise the issue set, and proceeds only if its own identifier is
listed. The module decides whether a given CA may issue for a name,
honoring the permissive default when no records exist, the
wildcard-specific set when relevant, and the empty value as a total
prohibition, so the check is the gate a CA must pass rather than a
suggestion.
"""

from __future__ import annotations


def may_issue(
    records: list[tuple[str, str]], ca_identifier: str, wildcard: bool
) -> bool:
    if not records:
        return True
    issuewild = [v for tag, v in records if tag == "issuewild"]
    issue = [v for tag, v in records if tag == "issue"]
    relevant = issuewild if (wildcard and issuewild) else issue
    if not relevant:
        return True
    permitted = {value.strip() for value in relevant}
    if "" in permitted or ";" in permitted:
        allowed = {v for v in permitted if v and v != ";"}
        return ca_identifier in allowed
    return ca_identifier in permitted
