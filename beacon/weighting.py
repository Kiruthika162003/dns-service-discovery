"""Weighted and locality-aware answers: nearest first, but never only.

Given several fit instances, which one to name first is a
policy question wearing a shuffle's clothes. Weighted choice
spreads load in proportion to declared capacity, and the
deterministic rotor makes it testable: the caller's request
counter walks a precomputed wheel where each instance appears
as many times as its weight, so a weight-3 instance answers
three of every four requests against a weight-1 peer, exactly,
not probably. Locality preference ranks same-zone instances
first because a cross-zone hop costs latency and often money,
but the preference is never a fence: when the local zone has
nobody fit, remote instances answer rather than nobody, and
the answer says it crossed zones, because silent cross-zone
traffic is how a network bill becomes a mystery novel. A
weight of zero is a legal state meaning drained: the instance
stays discoverable for operators and takes no new callers.
"""

from __future__ import annotations

from dataclasses import dataclass

from beacon.errors import Invalid, Missing


@dataclass(frozen=True)
class Endpoint:
    instance_id: str
    zone: str
    weight: int

    def __post_init__(self) -> None:
        if self.weight < 0:
            raise Invalid(
                f"{self.instance_id}: negative weight is not "
                "drained, it is nonsense"
            )


def build_wheel(endpoints: list[Endpoint]) -> list[str]:
    wheel = []
    for endpoint in sorted(
        endpoints, key=lambda held: held.instance_id
    ):
        wheel.extend(
            [endpoint.instance_id] * endpoint.weight
        )
    if not wheel:
        raise Invalid(
            "every endpoint is drained; a wheel of zero spokes "
            "spins nobody"
        )
    return wheel


def pick(
    endpoints: list[Endpoint], request_number: int
) -> str:
    wheel = build_wheel(endpoints)
    return wheel[request_number % len(wheel)]


def locality_order(
    endpoints: list[Endpoint], caller_zone: str
) -> tuple[list[Endpoint], str]:
    if not endpoints:
        raise Missing("no endpoints to order")
    local = [
        held for held in endpoints
        if held.zone == caller_zone and held.weight > 0
    ]
    remote = [
        held for held in endpoints
        if held.zone != caller_zone and held.weight > 0
    ]
    if local:
        return local + remote, (
            f"{len(local)} local endpoint(s) answer first; "
            f"{len(remote)} remote stand behind them"
        )
    if remote:
        return remote, (
            f"CROSSED ZONES: {caller_zone} has nobody fit, "
            f"{len(remote)} remote endpoint(s) answer, and "
            "saying so keeps the network bill from becoming "
            "a mystery novel"
        )
    raise Missing(
        "every endpoint everywhere is drained; the answer is "
        "nobody, said plainly"
    )


def share_report(
    endpoints: list[Endpoint], requests: int
) -> str:
    if requests < 1:
        raise Invalid("a share needs requests")
    served: dict[str, int] = {}
    for number in range(requests):
        chosen = pick(endpoints, number)
        served[chosen] = served.get(chosen, 0) + 1
    lines = [f"{requests} request(s) over the wheel:"]
    for instance_id in sorted(served):
        share = 100 * served[instance_id] // requests
        lines.append(
            f"  {instance_id}: {served[instance_id]} "
            f"({share}%)"
        )
    drained = [
        held.instance_id
        for held in endpoints
        if held.weight == 0
    ]
    for instance_id in drained:
        lines.append(
            f"  {instance_id}: drained, discoverable, and "
            "taking nobody"
        )
    return "\n".join(lines)
