"""A first zone: parsed from text, served, cached, and honest about no.

Run with: python -m examples.firstzone
"""

from __future__ import annotations

from beacon.errors import Missing, NoData
from beacon.names import Name
from beacon.resolver import Resolver
from beacon.zonefile import parse_zone

ZONE_TEXT = """\
$ORIGIN shop.example.
@ SOA 2026090801 3600 600 86400 120
www 300 A 192.0.2.10
api 300 A 192.0.2.20
blog 300 CNAME www
*.preview 60 A 192.0.2.99
"""


def main() -> int:
    zone = parse_zone(ZONE_TEXT)
    resolver = Resolver()
    resolver.host_zone(zone)

    outcome = resolver.resolve(
        Name.parse("www.shop.example"), "A", now=0
    )
    print(
        f"answer:  www -> {outcome.records[-1].value} "
        f"({outcome.upstream_queries} upstream)"
    )

    chained = resolver.resolve(
        Name.parse("blog.shop.example"), "A", now=1
    )
    print(
        f"alias:   blog -> {chained.records[0].rtype} -> "
        f"{chained.records[-1].value}"
    )

    wild = resolver.resolve(
        Name.parse("branch-7.preview.shop.example"), "A", now=2
    )
    print(f"wild:    branch-7.preview -> {wild.records[-1].value}")

    cached = resolver.resolve(
        Name.parse("www.shop.example"), "A", now=3
    )
    print(
        f"cache:   second ask from cache = {cached.from_cache}, "
        f"{cached.upstream_queries} upstream"
    )

    try:
        resolver.resolve(Name.parse("gone.shop.example"), "A", now=4)
    except Missing as refusal:
        print(f"nx:      {str(refusal).split(' (')[0]}")
    try:
        resolver.resolve(Name.parse("gone.shop.example"), "A", now=5)
    except Missing as refusal:
        remembered = "nothing travelled" in str(refusal)
        print(f"nx2:     remembered = {remembered}")

    try:
        resolver.resolve(Name.parse("www.shop.example"), "TXT", now=6)
    except NoData:
        print("nodata:  www exists, TXT does not; different no")

    print(f"ledger:  {resolver.descent_report()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
