"""The rebooking assistant as a LangGraph graph: find the fare rules, check seats, write the answer."""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from assistant import alerts, booking, llm
from assistant.data import PASSAGES
from assistant.retrieval import CHOSEN_RETRIEVER, RETRIEVERS

# How many times to ask the booking system before giving up and alerting someone.
MAX_BOOKING_ATTEMPTS = 3


class State(TypedDict, total=False):
    question: str
    flight: str
    passages: list
    sources: list
    seats: int | None
    booking_failed: bool
    booking_attempts: int
    alert_sent: bool
    answer: str


def find_rules(state):
    passages = RETRIEVERS[CHOSEN_RETRIEVER](state["question"], PASSAGES, 3)
    return {"passages": passages, "sources": [p["id"] for p in passages]}


def check_seats(state):
    attempts = state.get("booking_attempts", 0) + 1
    try:
        seats = booking.free_seats(state["flight"])
        return {"seats": seats, "booking_failed": False, "booking_attempts": attempts}
    except booking.BookingSystemDown:
        return {"seats": None, "booking_failed": True, "booking_attempts": attempts}


def make_after_check_seats(max_attempts: int):
    """Route after each try: retry while attempts remain, then alert instead of looping forever."""
    def after_check_seats(state):
        if not state["booking_failed"]:
            return "write_answer"
        if state["booking_attempts"] < max_attempts:
            return "check_seats"
        return "booking_down"
    return after_check_seats


def booking_down(state):
    """Booking system gave up: tell a human, then let write_answer reply without seats."""
    alerts.notify(f"Booking system down for flight {state['flight']} "
                  f"after {state['booking_attempts']} attempts")
    return {"alert_sent": True}


def write_answer(state):
    """Reads `sources` saved by find_rules two steps earlier, so the reply cites what it used."""
    answer = llm.write_answer(state["question"], state["passages"], state["seats"])
    sources = state.get("sources", [])
    if sources:
        answer = f"{answer} Sources: {', '.join(sources)}."
    return {"answer": answer}


def build(max_booking_attempts: int = MAX_BOOKING_ATTEMPTS):
    g = StateGraph(State)
    g.add_node("find_rules", find_rules)
    g.add_node("check_seats", check_seats)
    g.add_node("booking_down", booking_down)
    g.add_node("write_answer", write_answer)
    g.add_edge(START, "find_rules")
    g.add_edge("find_rules", "check_seats")
    g.add_conditional_edges("check_seats", make_after_check_seats(max_booking_attempts),
                            ["check_seats", "booking_down", "write_answer"])
    g.add_edge("booking_down", "write_answer")
    g.add_edge("write_answer", END)
    return g.compile()


def ask(question, flight):
    return build().invoke({"question": question, "flight": flight})
