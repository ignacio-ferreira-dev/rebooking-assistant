"""Behaviour of the graph beyond the exercise checks: retry cap, alert branch, sources kept in state."""

import unittest

from assistant import booking
from assistant.data import PASSAGES
from assistant.graph import build
from assistant.nodes import Node, make_route_after_check_seats


class FakeBooking:
    """Counts calls; raises BookingSystemDown for the first `failures` calls."""

    def __init__(self, failures: int = 0, seats: int = 4) -> None:
        self.calls = 0
        self.failures = failures
        self.seats = seats

    def __call__(self, flight: str) -> int:
        self.calls += 1
        if self.calls <= self.failures:
            raise booking.BookingSystemDown(flight)
        return self.seats


class Alerts:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def __call__(self, message: str) -> None:
        self.messages.append(message)


def run(max_attempts: int, failures: int) -> tuple[dict, FakeBooking, Alerts]:
    seats, alerts = FakeBooking(failures), Alerts()
    graph = build(max_attempts, free_seats=seats, notify=alerts)
    return graph.invoke({"question": "Is a cancelled flight free to change?", "flight": "UA100"}), seats, alerts


class RetryAndAlert(unittest.TestCase):
    def test_stops_at_max_attempts_and_alerts_once(self) -> None:
        for max_attempts in (1, 3, 5):
            with self.subTest(max_attempts=max_attempts):
                result, seats, alerts = run(max_attempts, failures=99)
                self.assertEqual(seats.calls, max_attempts)
                self.assertEqual(len(alerts.messages), 1)
                self.assertTrue(result["alert_sent"])
                self.assertIn("could not check seats", result["answer"])

    def test_recovers_before_the_limit_without_alerting(self) -> None:
        result, seats, alerts = run(max_attempts=3, failures=2)
        self.assertEqual(seats.calls, 3)
        self.assertEqual(alerts.messages, [])
        self.assertIn("Free seats on that flight: 4", result["answer"])

    def test_healthy_booking_is_called_once(self) -> None:
        result, seats, alerts = run(max_attempts=3, failures=0)
        self.assertEqual(seats.calls, 1)
        self.assertEqual(alerts.messages, [])
        self.assertNotIn("alert_sent", result)

    def test_rejects_non_positive_limit(self) -> None:
        with self.assertRaises(ValueError):
            make_route_after_check_seats(0)

    def test_router_routes(self) -> None:
        route = make_route_after_check_seats(3)
        self.assertEqual(route({"booking_failed": False, "booking_attempts": 1}), Node.WRITE_ANSWER)
        self.assertEqual(route({"booking_failed": True, "booking_attempts": 2}), Node.CHECK_SEATS)
        self.assertEqual(route({"booking_failed": True, "booking_attempts": 3}), Node.BOOKING_DOWN)


class Sources(unittest.TestCase):
    def test_sources_survive_until_the_answer_and_are_cited(self) -> None:
        result, _, _ = run(max_attempts=3, failures=99)
        self.assertEqual(result["sources"], [p["id"] for p in result["passages"]])
        self.assertIn("Sources: " + ", ".join(result["sources"]), result["answer"])

    def test_injected_retriever_is_used(self) -> None:
        def last_two(question: str, passages: list, k: int) -> list:
            return list(passages)[-2:]

        graph = build(retriever=last_two, free_seats=FakeBooking(), notify=Alerts())
        result = graph.invoke({"question": "anything", "flight": "UA100"})
        self.assertEqual(result["sources"], [p["id"] for p in PASSAGES[-2:]])


if __name__ == "__main__":
    unittest.main()
