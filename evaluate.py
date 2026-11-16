"""Measures both retrievers on the evaluation questions: python evaluate.py"""

from assistant.config import TOP_K
from assistant.data import EVAL, PASSAGES
from assistant.retrieval import RETRIEVERS, Retriever, recall_at_k


def score(retrieve: Retriever, k: int = TOP_K) -> float:
    """recall@k of one retriever over the evaluation set."""
    relevant = [e["relevant"] for e in EVAL]
    ranked = [[p["id"] for p in retrieve(e["question"], PASSAGES, k)] for e in EVAL]
    return recall_at_k(ranked, relevant, k)


def main() -> None:
    for name, retrieve in RETRIEVERS.items():
        print(f"{name}: recall@{TOP_K} = {score(retrieve):.2f}")


if __name__ == "__main__":
    main()
