"""The query log: sampled, summed, and read for the stories it tells.

Logging every query at volume drowns the disk to describe a
day nobody will read, so the log samples: one in N recorded
in full, every query counted in aggregates that cost bytes,
not gigabytes. The aggregates are chosen for the three
stories operators actually chase. Top talkers by source finds
the runaway client, the retry loop wearing a user's address.
The rcode mix finds the health story, and its sharpest
pattern gets named automatically: an NXDOMAIN share spiking
past the habitual noise is almost always a typo shipped in a
config, one misspelled hostname multiplied by every instance
of the deploying service, and the verdict says so with the
top missing name attached, because the log that only counts
is a meter while the log that names the probable cause is a
colleague.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid

SAMPLE_RATE = 100
NXDOMAIN_ALARM_SHARE = 30


@dataclass
class QueryLog:
    seen: int = 0
    sampled: list[str] = field(default_factory=list)
    by_source: dict[str, int] = field(default_factory=dict)
    by_rcode: dict[str, int] = field(default_factory=dict)
    missing_names: dict[str, int] = field(default_factory=dict)

    def record(
        self, source: str, name: str, rcode: str
    ) -> None:
        self.seen += 1
        self.by_source[source] = (
            self.by_source.get(source, 0) + 1
        )
        self.by_rcode[rcode] = self.by_rcode.get(rcode, 0) + 1
        if rcode == "NXDOMAIN":
            self.missing_names[name] = (
                self.missing_names.get(name, 0) + 1
            )
        if self.seen % SAMPLE_RATE == 1:
            self.sampled.append(f"{source} {name} {rcode}")

    def top_talkers(self, count: int) -> list[str]:
        if count < 1:
            raise Invalid("a top list needs a size")
        ranked = sorted(
            self.by_source.items(),
            key=lambda row: (-row[1], row[0]),
        )
        return [
            f"{source}: {queries} query(ies)"
            for source, queries in ranked[:count]
        ]

    def rcode_story(self) -> str:
        if not self.seen:
            raise Invalid("no queries, no story")
        nx = self.by_rcode.get("NXDOMAIN", 0)
        share = 100 * nx // self.seen
        line = (
            f"{self.seen} query(ies), NXDOMAIN share {share}%"
        )
        if share >= NXDOMAIN_ALARM_SHARE and self.missing_names:
            top_name, top_count = max(
                self.missing_names.items(),
                key=lambda row: (row[1], row[0]),
            )
            line += (
                f"; almost always a typo shipped in a config: "
                f"{top_name} asked {top_count} time(s), one "
                "misspelled hostname multiplied by every "
                "instance of the deploying service"
            )
        return line

    def storage_bill(self) -> str:
        return (
            f"{len(self.sampled)} full record(s) kept of "
            f"{self.seen}; the aggregates cost bytes, not "
            "gigabytes, and the sampled slice keeps the "
            "receipts"
        )
