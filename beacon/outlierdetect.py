"""Passive outlier ejection: the traffic itself is the health check.

Active probes ask synthetic questions on a schedule; passive
detection reads the answers real traffic already collects,
and its advantage is specificity: the instance that fails
only under production load, only for real payloads, looks
perfect to every probe and rotten in its live error rate. The
ejector compares each instance against its peers, not against
a fixed threshold, because a fleet-wide burn from a bad
deploy should page the deploy, not eject every instance one
by one; ejection is for the instance whose error rate stands
apart from the crowd's. The safety valve is the max-ejection
cap: no more than a fixed fraction of the fleet may be out
at once, because a detector that can eject everyone is a
detector that can cause the outage it guards against, and
when the cap binds, the verdict says which sick instances
stayed in rotation and why.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid

STAND_APART_FACTOR = 3
MAX_EJECTED_SHARE = 0.34


@dataclass
class OutlierEjector:
    error_rates: dict[str, float] = field(default_factory=dict)
    ejected: set[str] = field(default_factory=set)
    cap_bound: list[str] = field(default_factory=list)

    def observe(self, instance: str, error_rate: float) -> None:
        if not 0 <= error_rate <= 1:
            raise Invalid("error rates live between 0 and 1")
        self.error_rates[instance] = error_rate

    def _peer_median(self, instance: str) -> float:
        peers = sorted(
            rate
            for name, rate in self.error_rates.items()
            if name != instance
        )
        if not peers:
            raise Invalid("an instance with no peers has no crowd")
        return peers[len(peers) // 2]

    def evaluate(self) -> list[str]:
        if len(self.error_rates) < 3:
            raise Invalid(
                "outliers need a crowd of at least three"
            )
        verdicts = []
        cap = max(
            1,
            int(len(self.error_rates) * MAX_EJECTED_SHARE),
        )
        candidates = []
        for instance in sorted(self.error_rates):
            rate = self.error_rates[instance]
            median = self._peer_median(instance)
            if median == 0:
                stands_apart = rate > 0.05
            else:
                stands_apart = (
                    rate >= median * STAND_APART_FACTOR
                )
            if stands_apart:
                candidates.append((rate, instance))
        candidates.sort(reverse=True)
        for rate, instance in candidates:
            if len(self.ejected) < cap:
                self.ejected.add(instance)
                verdicts.append(
                    f"{instance} ejected at {rate:.0%} "
                    "against the crowd; the traffic itself "
                    "was the health check"
                )
            else:
                self.cap_bound.append(instance)
                verdicts.append(
                    f"{instance} stays IN rotation at "
                    f"{rate:.0%}: the ejection cap is bound, "
                    "because a detector that can eject "
                    "everyone can cause the outage it guards "
                    "against"
                )
        if not candidates:
            verdicts.append(
                "nobody stands apart; a fleet-wide burn "
                "pages the deploy, not the ejector"
            )
        return verdicts
