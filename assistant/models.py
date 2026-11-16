"""Typed shapes shared across the package: passages, evaluation items and the graph state."""

from typing import TypedDict


class Passage(TypedDict):
    id: str
    title: str
    text: str


class EvalItem(TypedDict):
    question: str
    relevant: str


class State(TypedDict, total=False):
    """Graph state. Every key a node returns must be declared here, or LangGraph drops it."""

    # Input
    question: str
    flight: str
    # find_rules
    passages: list[Passage]
    sources: list[str]
    # check_seats
    seats: int | None
    booking_failed: bool
    booking_attempts: int
    # booking_down
    alert_sent: bool
    # write_answer
    answer: str
