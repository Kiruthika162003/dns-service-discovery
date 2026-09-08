"""CDS and CDNSKEY: the child publishes the DS it wants, the parent acts only on proof.

Keeping the parent's DS record in step with a child's key-signing
key is the classic manual chore of DNSSEC, and the mistake it
invites is a broken chain of trust the moment the two drift. RFC
7344 automates it: the child publishes a CDS record stating the
delegation signer it wants installed, the parent polls for it,
and the parent updates the DS to match, but only under a rule
that keeps automation from becoming a hijack. The CDS must be
signed by a key already in the existing chain of trust, so a
newcomer cannot simply assert a new anchor; continuity, not
novelty, is what the parent trusts. RFC 8078 adds the one
deliberate exception, a CDS with algorithm zero, the signal to
delete the DS and take the child insecure, and the module treats
it as the distinct intent it is rather than a malformed record.
Mixing the delete sentinel with real records is refused, because
a child cannot both go insecure and rekey in the same breath.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid, Refused


@dataclass(frozen=True)
class CdsIntent:
    key_tag: int
    algorithm: int
    digest: str

    def is_delete_sentinel(self) -> bool:
        return self.algorithm == 0 and set(self.digest) <= {"0"}


def parent_apply(
    current_ds: set[tuple[int, int, str]],
    intents: list[CdsIntent],
    signed_by_current_chain: bool,
) -> set[tuple[int, int, str]]:
    if not intents:
        raise Invalid(
            "an empty CDS set is not an instruction; the parent "
            "does nothing rather than guess"
        )
    if not signed_by_current_chain:
        raise Refused(
            "the CDS is not signed by a key already in the chain "
            "of trust; the parent trusts continuity, not a "
            "newcomer asserting its own anchor"
        )
    deletes = [i for i in intents if i.is_delete_sentinel()]
    if deletes:
        if len(intents) != 1:
            raise Invalid(
                "the delete sentinel is mixed with real DS "
                "records; a child cannot go insecure and rekey in "
                "the same breath"
            )
        if not current_ds:
            raise Invalid(
                "the child asks to go insecure but no DS exists; "
                "it is already insecure and there is nothing to "
                "delete"
            )
        return set()
    return {(i.key_tag, i.algorithm, i.digest) for i in intents}
