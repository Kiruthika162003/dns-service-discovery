"""DNAME: redirect an entire subtree in one record, but deliberately not the owner name itself.

A CNAME aliases a single name, so aliasing a whole subtree, every
name under old.example to the matching name under new.example, would
need a CNAME per name, which is impossible when the names are not
known in advance. DNAME does it with one record. A DNAME at
old.example pointing to new.example rewrites any query for a
descendant, host.old.example, into the corresponding name under the
target, host.new.example, by replacing the DNAME's owner suffix with
the target, so the entire subtree is redirected by a single record
regardless of what names appear beneath it. The rule that surprises
people, and that the module enforces, is that a DNAME does not cover
its own owner name: a query for old.example itself is not rewritten
by the DNAME, only names strictly below it are, so redirecting a name
both at its apex and throughout its subtree requires a DNAME for the
descendants and a separate CNAME for the owner. A query outside the
subtree is untouched. The module rewrites a descendant name through
the DNAME, refuses to rewrite the owner itself, naming the CNAME it
needs instead, and refuses a name that does not lie under the owner
at all.
"""

from __future__ import annotations

from beacon.errors import Invalid


def rewrite(qname: str, owner: str, target: str) -> str:
    qname = qname.rstrip(".")
    owner_bare = owner.rstrip(".")
    target_bare = target.rstrip(".")
    if qname == owner_bare:
        raise Invalid(
            "a DNAME does not cover its own owner name; redirecting "
            "the owner itself needs a separate CNAME beside the DNAME"
        )
    if not qname.endswith("." + owner_bare):
        raise Invalid(
            f"{qname} is not under {owner}; a DNAME only rewrites "
            "names within its subtree"
        )
    prefix = qname[: -len(owner_bare)]
    return f"{prefix}{target_bare}."


def covers(qname: str, owner: str) -> bool:
    qname = qname.rstrip(".")
    owner_bare = owner.rstrip(".")
    return qname != owner_bare and qname.endswith("." + owner_bare)
