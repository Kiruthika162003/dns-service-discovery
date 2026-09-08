"""A secure day: chains of trust, key rollovers, minimized leaks, quieted lengths.

Run with: python -m examples.secureday
"""

from __future__ import annotations

from beacon.dohpadding import PaddingAnalysis
from beacon.dsdelegation import TrustChain
from beacon.keyrollover import Rollover
from beacon.names import Name
from beacon.qname import privacy_report


def morning_the_chain():
    chain = TrustChain()
    chain.add_zone(".", "root-fp", parent=None)
    chain.add_zone("com.", "com-fp", parent=".")
    chain.add_zone("shop.com.", "shop-fp", parent="com.")
    chain.publish_ds("com.", "com-fp")
    chain.publish_ds("shop.com.", "shop-fp")
    chain.trust_root(".")
    print(f"morning: {chain.validate('shop.com.')}")
    chain.zones["shop.com."].key_fingerprint = "rotated-fp"
    print(f"         {chain.validate('shop.com.').split(';')[0]}")


def midday_the_rollover():
    roll = Rollover(ttl=30)
    roll.pre_publish(now=0)
    roll.activate(now=30)
    print(f"midday:  {roll.retire(now=60).split(',')[0]}")
    print(f"         {roll.timeline_report().split(',')[0]}")


def afternoon_the_minimization():
    report = privacy_report(
        Name.parse("mail.eng.corp.example"), zone_cuts={2, 4}
    )
    print(f"afternoon: {report.split(';')[0]}")


def evening_the_padding():
    analysis = PaddingAnalysis(
        message_sizes=(43, 87, 91, 120, 200, 305)
    )
    print(f"evening: {analysis.privacy_report(128).split(';')[0]}")


def main() -> int:
    morning_the_chain()
    midday_the_rollover()
    afternoon_the_minimization()
    evening_the_padding()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
