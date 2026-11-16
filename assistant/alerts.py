"""Where the assistant reports outages. Logs for now; swap `notify` for SNS, PagerDuty or Slack in production."""

import logging

log = logging.getLogger("rebooking.alerts")


def notify(message: str) -> None:
    """Tell a human that something needs attention. Kept as a plain function so tests can patch it."""
    log.error(message)
