"""Response Policy Zones: a DNS firewall where the most specific rule wins.

A Response Policy Zone lets an operator override answers by
policy, to blackhole a malware domain, redirect a phishing name
to a warning page, or carve an exception through a broad block,
and the danger in such a system is precedence: when two rules
could match a name, which one fires. The module resolves it the
way RPZ does, by specificity, the rule whose trigger matches the
longest suffix of the query name wins, so a block on example. and
an allow on safe.example. do not fight, the allow simply governs
its narrower slice. Passthru is the rule that makes an allowlist
possible: it is an explicit decision to let a name resolve
normally, and because it is a rule like any other it can sit
beneath a broad block and win for its subtree, turning a
blanket deny into a deny-except. The default when nothing matches
is passthru, because a policy zone that silently blocked
everything it did not mention would be a firewall with the
default backwards, and the module makes that default explicit.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid

ACTIONS = ("nxdomain", "nodata", "passthru", "drop", "redirect")


@dataclass(frozen=True)
class PolicyRule:
    trigger: str
    action: str
    target: str = ""

    def __post_init__(self) -> None:
        if self.action not in ACTIONS:
            raise Invalid(
                f"{self.action!r} is not an RPZ action; it knows "
                f"{', '.join(ACTIONS)}"
            )
        if self.action == "redirect" and not self.target:
            raise Invalid(
                "a redirect must name where it redirects to; a "
                "rewrite with no target rewrites to nothing"
            )


def _matches(qname: str, trigger: str) -> bool:
    qname = qname.rstrip(".")
    trigger = trigger.rstrip(".")
    return qname == trigger or qname.endswith("." + trigger)


def evaluate(qname: str, rules: list[PolicyRule]) -> PolicyRule:
    matching = [rule for rule in rules if _matches(qname, rule.trigger)]
    if not matching:
        return PolicyRule(qname, "passthru")
    return max(matching, key=lambda rule: len(rule.trigger.rstrip(".")))
