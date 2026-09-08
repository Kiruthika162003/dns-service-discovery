"""A saga: a long transaction as steps with compensators, trading atomicity for availability.

Some workflows span services and cannot hold a single lock across
all of them for the time they take, register the service, create its
DNS record, provision its certificate, so a classic transaction is
impossible. A saga runs them as a sequence of independent steps,
each with a compensating action that undoes it, and if a step fails
the saga does not roll back with a database's atomicity, it runs the
compensators for the already-completed steps in reverse order, so
the created certificate is revoked, then the DNS record deleted, then
the registration removed. What this buys is availability, no global
lock, each step commits on its own, and what it costs is stated
plainly: the saga is not atomic, its intermediate states are visible
to the outside world while it runs, and compensation is
application-defined and can itself fail, so a saga reaches
eventual consistency rather than the all-or-nothing a transaction
guarantees. The module runs the steps to a given failure point and
returns the compensation order, the reverse of what completed, so
the undo path is explicit rather than assumed to exist.
"""

from __future__ import annotations

from beacon.errors import Invalid


def execute(steps: list[str], fail_at: int | None) -> tuple[str, list[str]]:
    if fail_at is not None and not 0 <= fail_at < len(steps):
        raise Invalid(
            f"the failure point {fail_at} is outside the {len(steps)} "
            "steps; a saga can only fail at a step it has"
        )
    if fail_at is None:
        return "committed", []
    completed = steps[:fail_at]
    return "compensated", list(reversed(completed))
