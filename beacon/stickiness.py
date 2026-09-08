"""Session affinity: keep a user on one backend, but not past its death.

Some services keep per-session state on the backend that first
served a user, so scattering that user's later requests across
the fleet loses the session. Affinity pins a session key to a
backend, and the tension this module holds is between two
promises that fight: stickiness wants the user to keep the
same backend forever, and availability wants the user moved
the instant that backend dies. The rule that resolves the
fight is that health outranks affinity: a pinned backend that
is still alive keeps its session, and a pinned backend that
has died releases every session it held to be re-pinned
elsewhere, because honoring affinity to a dead backend is
serving errors politely. The rebalance on a backend's return
is deliberately incomplete, only new sessions land on the
recovered backend while existing pins stay put, because moving
live sessions back just to restore symmetry loses the very
state affinity exists to preserve.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from beacon.errors import Invalid, Missing


@dataclass
class AffinityTable:
    healthy: set[str] = field(default_factory=set)
    pins: dict[str, str] = field(default_factory=dict)
    orphaned: set[str] = field(default_factory=set)
    repins: int = 0
    honored: int = 0

    def add_backend(self, backend: str) -> None:
        self.healthy.add(backend)

    def mark_down(self, backend: str) -> str:
        if backend not in self.healthy:
            raise Invalid(f"{backend} was not healthy")
        self.healthy.discard(backend)
        released = [
            key
            for key, pinned in self.pins.items()
            if pinned == backend
        ]
        for key in released:
            del self.pins[key]
            self.orphaned.add(key)
        return (
            f"{backend} down: released {len(released)} "
            "session(s) to re-pin, because affinity to a dead "
            "backend is serving errors politely"
        )

    def route(self, session_key: str) -> str:
        if not self.healthy:
            raise Missing(
                "no healthy backend to pin to; the fleet is "
                "down and affinity cannot conjure a survivor"
            )
        pinned = self.pins.get(session_key)
        if pinned is not None and pinned in self.healthy:
            self.honored += 1
            return (
                f"{session_key} -> {pinned} (affinity held; "
                "the session lives where its state lives)"
            )
        chosen = min(
            self.healthy,
            key=lambda backend: (
                sum(
                    1
                    for value in self.pins.values()
                    if value == backend
                ),
                backend,
            ),
        )
        self.pins[session_key] = chosen
        self.repins += 1
        if session_key in self.orphaned:
            reason = "its backend died"
            self.orphaned.discard(session_key)
        else:
            reason = "first sight"
        return (
            f"{session_key} -> {chosen} (re-pinned, {reason}; "
            "health outranks affinity)"
        )

    def ledger(self) -> str:
        return (
            f"{self.honored} affinity honor(s), "
            f"{self.repins} re-pin(s); the re-pins are "
            "availability winning exactly when it should"
        )
