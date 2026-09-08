"""Zone transfers: the secondary asks for everything or just the difference.

A secondary keeps a copy of the zone and the transfer protocol
is how the copy stays honest. Full transfer ships every record
and always works; incremental transfer ships only the deltas
between two serials and only works while the primary still
remembers the journey, so the journal is a window, not an
archive, and a secondary that fell too far behind is told to
ask for everything rather than being handed a gap dressed as a
delta. The serial gate runs on circle arithmetic: a transfer
request bearing a serial not older than the primary's is
answered with not-modified and zero records, which is most
transfers on a quiet zone and the reason refresh polling is
affordable. The ledger prices the economy: records shipped
incrementally against what full transfers would have moved,
because the journal's whole salary is that difference.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid, Missing
from beacon.records import Record
from beacon.serialmath import check_serial, newer

JOURNAL_WINDOW = 8


@dataclass
class Delta:
    from_serial: int
    to_serial: int
    added: list[Record]
    removed: list[Record]


@dataclass
class TransferPrimary:
    serial: int
    records: list[Record] = field(default_factory=list)
    journal: list[Delta] = field(default_factory=list)
    incremental_shipped: int = 0
    full_shipped: int = 0
    not_modified_served: int = 0

    def publish(
        self,
        new_serial: int,
        added: list[Record],
        removed: list[Record],
    ) -> str:
        check_serial(new_serial)
        if not newer(new_serial, self.serial):
            raise Invalid(
                f"serial {new_serial} is not newer than "
                f"{self.serial}; content moved but the serial "
                "did not, and secondaries would sleep through "
                "the change"
            )
        self.journal.append(
            Delta(
                from_serial=self.serial,
                to_serial=new_serial,
                added=list(added),
                removed=list(removed),
            )
        )
        if len(self.journal) > JOURNAL_WINDOW:
            self.journal.pop(0)
        for record in removed:
            self.records.remove(record)
        self.records.extend(added)
        self.serial = new_serial
        return f"published serial {new_serial}"

    def full_transfer(self) -> tuple[int, list[Record]]:
        self.full_shipped += len(self.records)
        return self.serial, list(self.records)

    def incremental_transfer(
        self, have_serial: int
    ) -> tuple[str, list[Delta]]:
        check_serial(have_serial)
        if not newer(self.serial, have_serial):
            self.not_modified_served += 1
            return "NOT-MODIFIED", []
        chain = []
        cursor = have_serial
        for delta in self.journal:
            if delta.from_serial == cursor:
                chain.append(delta)
                cursor = delta.to_serial
        if cursor != self.serial or not chain:
            raise Missing(
                f"the journal no longer remembers the road "
                f"from {have_serial}; ask for everything, "
                "because a gap dressed as a delta corrupts "
                "the copy it claims to update"
            )
        self.incremental_shipped += sum(
            len(delta.added) + len(delta.removed)
            for delta in chain
        )
        return "DELTAS", chain

    def economy(self) -> str:
        return (
            f"{self.incremental_shipped} record(s) shipped "
            f"incrementally, {self.full_shipped} in full "
            f"transfers, {self.not_modified_served} "
            "not-modified: the journal's salary is the "
            "difference between the first two numbers"
        )
