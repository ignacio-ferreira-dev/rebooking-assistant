"""The HTTP service: validation, happy path, outage path, and a real socket round trip."""

import json
import threading
import unittest
import urllib.error
import urllib.request
from http import HTTPStatus
from http.server import ThreadingHTTPServer

import service


class AnswerFunction(unittest.TestCase):
    def test_happy_path(self) -> None:
        status, body = service.answer({"question": "Is a cancelled flight free to change?", "flight": "ua100"})
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(len(body["sources"]), 3)
        self.assertTrue(body["booking_available"])

    def test_booking_outage_is_reported_not_raised(self) -> None:
        status, body = service.answer({"question": "Earlier flight today?", "flight": "UA900"})
        self.assertEqual(status, HTTPStatus.OK)
        self.assertFalse(body["booking_available"])
        self.assertIn("could not check seats", body["answer"])

    def test_validation(self) -> None:
        for payload in (None, [], {}, {"question": "x"}, {"question": " ", "flight": "UA100"},
                        {"question": "x", "flight": 100}):
            with self.subTest(payload=payload):
                status, body = service.answer(payload)
                self.assertEqual(status, HTTPStatus.BAD_REQUEST)
                self.assertIn("error", body)


class OverHttp(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), service.Handler)
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()

    def request(self, path: str, body: bytes | None = None) -> tuple[int, dict]:
        req = urllib.request.Request(self.base + path, data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as err:
            return err.code, json.loads(err.read())

    def test_health(self) -> None:
        self.assertEqual(self.request("/health"), (200, {"status": "ok"}))

    def test_ask(self) -> None:
        status, body = self.request("/ask", json.dumps({"question": "Refund?", "flight": "UA100"}).encode())
        self.assertEqual(status, 200)
        self.assertIn("answer", body)

    def test_bad_json(self) -> None:
        self.assertEqual(self.request("/ask", b"{not json")[0], 400)

    def test_unknown_path(self) -> None:
        self.assertEqual(self.request("/nope")[0], 404)


if __name__ == "__main__":
    unittest.main()
