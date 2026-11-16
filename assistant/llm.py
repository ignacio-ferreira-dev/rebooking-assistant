"""A fake, deterministic LLM so the exercise runs without API keys. It writes the answer from what it is given."""

from assistant.models import Passage

NO_RULE = "No rule found."
SEATS_UNKNOWN = "I could not check seats right now."


def write_answer(question: str, passages: list[Passage], seats: int | None) -> str:
    """Quote the top passage and the seat count; `seats=None` means the booking system could not be reached."""
    rule = f"{passages[0]['title']}: {passages[0]['text']}" if passages else NO_RULE
    if seats is None:
        return f"{rule} {SEATS_UNKNOWN}"
    return f"{rule} Free seats on that flight: {seats}."
