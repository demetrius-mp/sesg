"""Protocol for similar a words generator."""

from typing import Protocol


class SimilarWordsGenerator(Protocol):
    """Protocol for similar a words generator."""

    def __call__(self, word: str) -> list[str]:  # pragma: no cover
        """Interface of a function that generates similar words.

        Args:
            word (str): Word from which to find similar words.

        Returns:
            List of similar words.
        """
        raise NotImplementedError()
