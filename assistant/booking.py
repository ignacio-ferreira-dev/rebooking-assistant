"""Stand-in for the airline's booking system. Flights starting with UA9 are on a server that is down."""

from typing import Final

DOWN_PREFIX: Final[str] = "UA9"
SEATS: Final[dict[str, int]] = {"UA100": 4, "UA200": 0, "UA300": 12}


class BookingSystemDown(Exception):
    """The booking system did not answer. Transient: worth retrying."""


def free_seats(flight: str) -> int:
    """Free seats on `flight`; unknown flights have 0. Raises BookingSystemDown for UA9xx flights."""
    if flight.startswith(DOWN_PREFIX):
        raise BookingSystemDown(flight)
    return SEATS.get(flight, 0)
