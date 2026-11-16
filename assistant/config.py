"""Tunable settings in one place, so behaviour changes do not require touching graph code."""

from typing import Final

# How many times to ask the booking system before giving up and alerting someone.
MAX_BOOKING_ATTEMPTS: Final[int] = 3

# How many fare-rule passages to retrieve per question (also the k used for recall@k).
TOP_K: Final[int] = 3
