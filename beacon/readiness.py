"""Liveness and readiness answer different questions: one restarts, the other reroutes.

Two health signals are constantly confused, and the confusion
causes outages in opposite directions. Liveness asks is this
process broken beyond recovery, and a failed liveness check means
restart it, because only a fresh process will help. Readiness asks
can this instance serve right now, and a failed readiness check
means stop routing to it, but do not restart it, because it may
recover on its own once a dependency returns or a warmup finishes.
Wiring them backwards is the classic disaster: put a shared
database check behind liveness and the moment the database blips
every instance fails liveness at once and the whole fleet
restarts, turning a brief dependency hiccup into a full outage,
when a readiness check would merely have paused routing until the
database came back. The module maps the two probes to the two
actions, restart on dead, deroute on unready, serve on both, and
flags a liveness probe that depends on a shared resource as the
cascade waiting to happen that it is.
"""

from __future__ import annotations

from beacon.errors import Invalid


def action(alive: bool, ready: bool) -> str:
    if not alive:
        return "restart"
    if not ready:
        return "remove-from-lb"
    return "serve"


def routable(alive: bool, ready: bool) -> bool:
    return action(alive, ready) == "serve"


def audit_liveness(depends_on_shared_resource: bool) -> str:
    if depends_on_shared_resource:
        raise Invalid(
            "a liveness probe that checks a shared resource "
            "restarts the whole fleet when that resource blips; "
            "check shared dependencies with readiness, which only "
            "pauses routing"
        )
    return "liveness checks only this process; safe from cascades"
