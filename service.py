"""HTTP service for the assistant, ready for a container platform such as ECS Fargate.

    GET  /health  -> 200 {"status": "ok"}                (load balancer / container health check)
    POST /ask     -> 200 {"answer": ..., "sources": [...]} body: {"question": "...", "flight": "UA100"}

Stdlib only (no new dependencies). Listens on $PORT (default 8080) and stops cleanly on SIGTERM,
which is how ECS stops a task during deploys and scale-in.
"""

from __future__ import annotations

import json
import logging
import os
import signal
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from assistant.graph import build

MAX_BODY_BYTES = 10_000

log = logging.getLogger("rebooking.service")
GRAPH = build()  # compiled once per process; invocations do not share state


def answer(payload: Any) -> tuple[HTTPStatus, dict[str, Any]]:
    """Validate the request body and run the graph. Pure function, so it is easy to test without a socket."""
    if not isinstance(payload, dict):
        return HTTPStatus.BAD_REQUEST, {"error": "body must be a JSON object"}
    question, flight = payload.get("question"), payload.get("flight")
    if not isinstance(question, str) or not question.strip():
        return HTTPStatus.BAD_REQUEST, {"error": "'question' must be a non-empty string"}
    if not isinstance(flight, str) or not flight.strip():
        return HTTPStatus.BAD_REQUEST, {"error": "'flight' must be a non-empty string"}
    result = GRAPH.invoke({"question": question.strip(), "flight": flight.strip().upper()})
    return HTTPStatus.OK, {"answer": result["answer"], "sources": result.get("sources", []),
                           "booking_available": not result.get("alert_sent", False)}


class Handler(BaseHTTPRequestHandler):
    server_version = "rebooking-assistant"

    def _send(self, status: HTTPStatus, body: dict[str, Any]) -> None:
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802 (name required by BaseHTTPRequestHandler)
        if self.path == "/health":
            self._send(HTTPStatus.OK, {"status": "ok"})
        else:
            self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/ask":
            self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY_BYTES:
            self._send(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "body too large"})
            return
        try:
            payload = json.loads(self.rfile.read(length) or b"null")
        except json.JSONDecodeError:
            self._send(HTTPStatus.BAD_REQUEST, {"error": "invalid JSON"})
            return
        try:
            status, body = answer(payload)
        except Exception:  # never leak internals to the client; the log keeps the traceback
            log.exception("ask failed")
            status, body = HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "internal error"}
        self._send(status, body)

    def log_message(self, fmt: str, *args: Any) -> None:
        log.info("%s %s", self.address_string(), fmt % args)


class JsonFormatter(logging.Formatter):
    """One valid JSON object per line, so CloudWatch Logs Insights can filter by field."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {"time": self.formatTime(record), "level": record.levelname,
                 "logger": record.name, "message": record.getMessage()}
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry)


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=level, handlers=[handler])


def serve(port: int) -> None:
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    # SIGTERM -> shutdown() must run off the serving thread, or it deadlocks.
    signal.signal(signal.SIGTERM, lambda *_: threading.Thread(target=server.shutdown).start())
    log.info("listening on :%d", port)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        log.info("stopped")


if __name__ == "__main__":
    configure_logging(os.environ.get("LOG_LEVEL", "INFO"))
    serve(int(os.environ.get("PORT", "8080")))
