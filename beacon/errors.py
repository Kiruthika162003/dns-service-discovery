"""The error family: every refusal in this resolver descends from one name."""

from __future__ import annotations


class BeaconError(Exception):
    """Base for everything this system refuses to do."""


class Invalid(BeaconError):
    """The request contradicts itself or the rules of names."""


class Missing(BeaconError):
    """The thing addressed does not exist at all."""


class NoData(BeaconError):
    """The name exists, but not with the record type asked for."""


class Loop(BeaconError):
    """Following the chain would circle forever."""


class Expired(BeaconError):
    """The answer was true once and its time has run out."""


class Refused(BeaconError):
    """The server will not answer this asker about this zone."""


class Lagging(BeaconError):
    """The watcher has fallen off the retained window."""
