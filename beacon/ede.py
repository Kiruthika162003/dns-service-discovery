"""Extended DNS Errors: the same SERVFAIL, finally told why.

A bare SERVFAIL is a shrug: the resolver failed and will not
say whether the zone is unsigned garbage, deliberately blocked,
served stale under duress, or simply unreachable, so the client
cannot tell a censorship wall from a broken link and retries
both identically. RFC 8914 attaches an extended error to the
response, a numeric info-code and a short human note, and the
crucial rule the module enforces is that the extended error is
advisory: it annotates the rcode, it never changes it, because
a resolver that downgraded SERVFAIL to NOERROR just because it
could explain the failure would be lying with extra words. The
codes divide into two moral categories the report keeps apart,
the failures that are the resolver's or network's fault and the
refusals that are a deliberate policy, since a client should
back off from the first and never retry the second.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid

INFO_CODES = {
    0: ("other", "network"),
    3: ("stale-answer", "network"),
    6: ("dnssec-bogus", "network"),
    7: ("signature-expired", "network"),
    10: ("not-authoritative", "network"),
    15: ("blocked", "policy"),
    16: ("censored", "policy"),
    17: ("filtered", "policy"),
    18: ("prohibited", "policy"),
}

RETRYABLE_RCODES = {"SERVFAIL", "REFUSED"}


@dataclass(frozen=True)
class ExtendedError:
    rcode: str
    info_code: int
    extra_text: str = ""

    def __post_init__(self) -> None:
        if self.info_code not in INFO_CODES:
            raise Invalid(
                f"info-code {self.info_code} is not one this "
                "resolver assigns; an unknown code is worse than "
                "no annotation because it invents a reason"
            )

    @property
    def purport(self) -> str:
        return INFO_CODES[self.info_code][0]

    @property
    def fault(self) -> str:
        return INFO_CODES[self.info_code][1]

    def is_policy(self) -> bool:
        return self.fault == "policy"

    def should_retry(self) -> bool:
        if self.is_policy():
            return False
        return self.rcode in RETRYABLE_RCODES

    def render(self) -> str:
        note = f" ({self.extra_text})" if self.extra_text else ""
        advice = (
            "do not retry; this is a deliberate policy"
            if self.is_policy()
            else "retry is allowed; this is a fault, not a refusal"
        )
        return (
            f"{self.rcode} + EDE {self.info_code} "
            f"{self.purport}{note}: {advice}"
        )


def annotate(rcode: str, info_code: int, note: str = "") -> ExtendedError:
    return ExtendedError(rcode, info_code, note)


def divide(errors: list[ExtendedError]) -> str:
    policy = sum(1 for e in errors if e.is_policy())
    faults = len(errors) - policy
    return (
        f"{faults} fault(s) worth retrying, {policy} "
        "policy refusal(s) that must not be retried; the "
        "extended error never changes the rcode, it only "
        "explains it"
    )
