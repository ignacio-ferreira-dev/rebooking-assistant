"""Two simple retrievers (no embeddings, so it runs offline) and the one the assistant uses."""

import re
from collections.abc import Callable, Sequence

from assistant.metrics import recall_at_k  # re-exported: evaluate.py and tests/ import it from here
from assistant.models import Passage

__all__ = ["RETRIEVERS", "CHOSEN_RETRIEVER", "Retriever", "by_title", "by_title_and_text", "recall_at_k", "words"]

Retriever = Callable[[str, Sequence[Passage], int], list[Passage]]

STOPWORDS = {"a", "an", "the", "is", "are", "can", "to", "for", "of", "on", "in", "and", "or", "what", "how", "much",
             "does", "do", "he", "she", "we", "our", "it", "be", "may", "if", "there", "where", "after", "with", "by"}


def words(text: str) -> list[str]:
    """Lower-cased words of `text`, without stopwords."""
    return [w for w in re.findall(r"[a-z]+", text.lower()) if w not in STOPWORDS]


def _rank_by_overlap(question: str, passages: Sequence[Passage], k: int,
                     field_text: Callable[[Passage], str]) -> list[Passage]:
    """Top k passages by how many question words appear in `field_text(passage)`. Ties keep input order."""
    q = set(words(question))
    return sorted(passages, key=lambda p: -len(q & set(words(field_text(p)))))[:k]


def by_title(question: str, passages: Sequence[Passage], k: int) -> list[Passage]:
    """Ranks passages by the words they share with the question, looking only at the title."""
    return _rank_by_overlap(question, passages, k, lambda p: p["title"])


def by_title_and_text(question: str, passages: Sequence[Passage], k: int) -> list[Passage]:
    """Ranks passages by the words they share with the question, looking at the title and the text."""
    return _rank_by_overlap(question, passages, k, lambda p: f"{p['title']} {p['text']}")


RETRIEVERS: dict[str, Retriever] = {"by_title": by_title, "by_title_and_text": by_title_and_text}

# Chosen by measuring both with recall@3 (python evaluate.py): by_title_and_text 1.00, by_title 0.80.
CHOSEN_RETRIEVER = "by_title_and_text"
