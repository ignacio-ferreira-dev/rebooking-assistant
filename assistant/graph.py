"""The rebooking assistant as a LangGraph graph: find the fare rules, check seats, write the answer.

    find_rules -> check_seats --ok--> write_answer -> END
                    ^   |                 ^
                    +---+ retry           |
                        +--> booking_down-+   (after max attempts: alert a human)
"""

from collections.abc import Sequence

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from assistant import config
from assistant.alerts import Notifier
from assistant.data import PASSAGES
from assistant.models import Passage, State
from assistant.nodes import (Node, SeatLookup, make_booking_down, make_check_seats, make_find_rules,
                             make_route_after_check_seats, write_answer)
from assistant.retrieval import CHOSEN_RETRIEVER, RETRIEVERS, Retriever


def build(max_booking_attempts: int = config.MAX_BOOKING_ATTEMPTS, *,
          retriever: Retriever | None = None,
          passages: Sequence[Passage] = PASSAGES,
          top_k: int = config.TOP_K,
          free_seats: SeatLookup | None = None,
          notify: Notifier | None = None) -> CompiledStateGraph:
    """Wire the graph. Every dependency has a production default and can be replaced in tests."""
    g = StateGraph(State)
    g.add_node(Node.FIND_RULES, make_find_rules(retriever or RETRIEVERS[CHOSEN_RETRIEVER], passages, top_k))
    g.add_node(Node.CHECK_SEATS, make_check_seats(free_seats))
    g.add_node(Node.BOOKING_DOWN, make_booking_down(notify))
    g.add_node(Node.WRITE_ANSWER, write_answer)

    g.add_edge(START, Node.FIND_RULES)
    g.add_edge(Node.FIND_RULES, Node.CHECK_SEATS)
    g.add_conditional_edges(Node.CHECK_SEATS, make_route_after_check_seats(max_booking_attempts),
                            [Node.CHECK_SEATS, Node.BOOKING_DOWN, Node.WRITE_ANSWER])
    g.add_edge(Node.BOOKING_DOWN, Node.WRITE_ANSWER)
    g.add_edge(Node.WRITE_ANSWER, END)
    return g.compile()


def ask(question: str, flight: str) -> State:
    """Answer one gate-agent question about one flight."""
    return build().invoke({"question": question, "flight": flight})
