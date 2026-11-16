"""Retrieval quality measures, kept apart from the retrievers they judge."""

from collections.abc import Sequence


def recall_at_k(ranked_ids: Sequence[Sequence[str]], relevant_ids: Sequence[str], k: int) -> float:
    """Share of questions whose relevant passage id is among the first k ids ranked for that question.

    ranked_ids:   one list of passage ids per question, best first, e.g. [["FR-03", "FR-01"], ["FR-07", "FR-04"]]
    relevant_ids: the right passage id for each question, e.g. ["FR-01", "FR-02"]
    Returns a number from 0.0 to 1.0. In the example, recall_at_k(..., k=2) is 0.5.
    An empty question set scores 0.0 instead of dividing by zero.
    """
    if not relevant_ids:
        return 0.0
    hits = sum(relevant in ranked[:k] for ranked, relevant in zip(ranked_ids, relevant_ids))
    return hits / len(relevant_ids)
