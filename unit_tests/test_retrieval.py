"""recall_at_k edge cases and the retriever choice."""

import unittest

import evaluate
from assistant.metrics import recall_at_k
from assistant.retrieval import CHOSEN_RETRIEVER, RETRIEVERS


class RecallAtK(unittest.TestCase):
    def test_docstring_example(self) -> None:
        self.assertEqual(recall_at_k([["FR-03", "FR-01"], ["FR-07", "FR-04"]], ["FR-01", "FR-02"], 2), 0.5)

    def test_only_first_k_count(self) -> None:
        self.assertEqual(recall_at_k([["A", "B", "C"]], ["C"], 2), 0.0)
        self.assertEqual(recall_at_k([["A", "B", "C"]], ["C"], 3), 1.0)

    def test_k_larger_than_ranking(self) -> None:
        self.assertEqual(recall_at_k([["A"]], ["A"], 10), 1.0)

    def test_empty_question_set(self) -> None:
        self.assertEqual(recall_at_k([], [], 3), 0.0)


class Choice(unittest.TestCase):
    def test_chosen_retriever_has_the_best_recall(self) -> None:
        scores = {name: evaluate.score(r) for name, r in RETRIEVERS.items()}
        self.assertEqual(CHOSEN_RETRIEVER, max(scores, key=scores.get), scores)


if __name__ == "__main__":
    unittest.main()
