"""Graph nodes and the router. Each node reads the state and returns only the keys it changes.

Dependencies (retriever, booking lookup, notifier) are injected through small factories so tests can swap them.
When left as None they are looked up at call time, so `mock.patch` on the module attribute still works.
"""

from collections.abc import Callable, Sequence
from typing import Final

from assistant import alerts, booking, llm
from assistant.alerts import Notifier
from assistant.models import Passage, State
from assistant.retrieval import Retriever

SeatLookup = Callable[[str], int]
NodeFn = Callable[[State], State]


class Node:
    """Node names in one place, so edges and routes cannot drift apart through a typo."""

    FIND_RULES: Final = "find_rules"
    CHECK_SEATS: Final = "check_seats"
    BOOKING_DOWN: Final = "booking_down"
    WRITE_ANSWER: Final = "write_answer"


def make_find_rules(retriever: Retriever, passages: Sequence[Passage], k: int) -> NodeFn:
    def find_rules(state: State) -> State:
        """Retrieve the top k fare rules and keep their ids in `sources` for the rest of the run."""
        found = retriever(state["question"], passages, k)
        return {"passages": found, "sources": [p["id"] for p in found]}
    return find_rules


def make_check_seats(free_seats: SeatLookup | None = None) -> NodeFn:
    def check_seats(state: State) -> State:
        """Ask the booking system once and count the attempt; an outage is recorded, not raised."""
        lookup = free_seats or booking.free_seats
        attempts = state.get("booking_attempts", 0) + 1
        try:
            return {"seats": lookup(state["flight"]), "booking_failed": False, "booking_attempts": attempts}
        except booking.BookingSystemDown:
            return {"seats": None, "booking_failed": True, "booking_attempts": attempts}
    return check_seats


def make_route_after_check_seats(max_attempts: int) -> Callable[[State], str]:
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    def route_after_check_seats(state: State) -> str:
        """Answer on success, retry while attempts remain, then hand over to the alert node."""
        if not state["booking_failed"]:
            return Node.WRITE_ANSWER
        if state["booking_attempts"] < max_attempts:
            return Node.CHECK_SEATS
        return Node.BOOKING_DOWN
    return route_after_check_seats


def make_booking_down(notify: Notifier | None = None) -> NodeFn:
    def booking_down(state: State) -> State:
        """Retries are exhausted: tell a human, then let write_answer reply without seats."""
        send = notify or alerts.notify
        send(f"Booking system down for flight {state['flight']} after {state['booking_attempts']} attempts")
        return {"alert_sent": True}
    return booking_down


def write_answer(state: State) -> State:
    """Write the reply and cite the passage ids that find_rules saved in `sources`."""
    answer = llm.write_answer(state["question"], state["passages"], state["seats"])
    sources = state.get("sources", [])
    if sources:
        answer = f"{answer} Sources: {', '.join(sources)}."
    return {"answer": answer}
