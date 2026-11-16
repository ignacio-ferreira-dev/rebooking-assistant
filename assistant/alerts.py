"""Where the assistant reports outages. Logs for now; swap `notify` for SNS, PagerDuty or Slack in production."""

import logging
from typing import Callable

Notifier = Callable[[str], None]

log = logging.getLogger("rebooking.alerts")


def notify(message: str) -> None:
    """Tell a human that something needs attention. A plain function, so it is easy to replace or patch."""
    log.error(message)
