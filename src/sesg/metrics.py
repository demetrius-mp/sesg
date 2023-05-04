"""Metrics module.

This module is responsible to provide metrics of a search string
performance, given the number of Scopus results found, number of GS
studies found in the Scopus results, and other informations.
"""  # noqa: E501

from dataclasses import dataclass
from typing import Any

from rapidfuzz.distance import Levenshtein


@dataclass
class Metrics:
    """Data container for metrics calculations.

    Args:
        gs_size (int): Number of studies in the GS.
        n_scopus_results (int): Total number of Scopus results. Don't set the 5_000 boundary, as this class will automatically use the correct value when calculating the metrics.
        n_qgs_studies_in_scopus (int): Number of QGS studies that were found in Scopus.
        n_gs_studies_in_scopus (int): Number of GS studies that were found in Scopus.
        n_gs_studies_in_scopus_and_bsb (int): Number of GS studies that were found in Scopus, and can be found via backward snowballing on the start set.
        n_gs_studies_in_scopus_and_bsb_and_fsb (int): Number of GS studies that were found in Scopus, and can be found via backward or forward snowballing on the start set.

    Examples:
        >>> metrics = Metrics(
        ...     gs_size=15,
        ...     n_scopus_results=13,
        ...     n_qgs_studies_in_scopus=2,
        ...     n_gs_studies_in_scopus=2,
        ...     n_gs_studies_in_scopus_and_bsb=8,
        ...     n_gs_studies_in_scopus_and_bsb_and_fsb=15,
        ... )
        >>> metrics.scopus_and_bsb_and_fsb_recall
        1.0
    """  # noqa: E501

    gs_size: int
    n_scopus_results: int

    n_qgs_studies_in_scopus: int
    n_gs_studies_in_scopus: int
    n_gs_studies_in_scopus_and_bsb: int
    n_gs_studies_in_scopus_and_bsb_and_fsb: int

    @property
    def n_scopus_results_with_limit(self):
        """Limits the number of results up to 5000."""
        return min(5000, self.n_scopus_results)

    @property
    def scopus_precision(self):
        """Measures the precision using the number of GS studies found in Scopus, and the number of Scopus Results with an upper limit of 5000.

        If no Scopus result were found, will return 0.
        """  # noqa: E501
        if self.n_scopus_results_with_limit == 0:
            return 0

        return self.n_gs_studies_in_scopus / self.n_scopus_results_with_limit

    @property
    def scopus_recall(self):
        """Measures the recall using the number of GS studies found in Scopus, and the GS size."""  # noqa: E501
        return self.n_gs_studies_in_scopus / self.gs_size

    @property
    def scopus_f1_score(self):
        """Measures the F1-Score using `scopus_precision` and `scopus_recall`.

        If the recall and the precision are both 0 (which happens when
        no GS studies were found in Scopus results, and when no Scopus
        results were found, respectively), will return 0.
        """
        precision = self.scopus_precision
        recall = self.scopus_recall

        numerator = 2 * precision * recall
        denominator = precision + recall

        if denominator == 0:
            return 0

        return numerator / denominator

    @property
    def scopus_and_bsb_recall(self):
        """Measures the recall using the number of GS studies found in Scopus + number of studies found with Backward Snowballing, and the GS size."""  # noqa: E501
        return self.n_gs_studies_in_scopus_and_bsb / self.gs_size

    @property
    def scopus_and_bsb_and_fsb_recall(self):
        """Measures the recall using the number of GS studies found in Scopus + number of studies found with Backward Snowballing, + number of studiesfound with Forward Snowballing, and the GS size."""  # noqa: E501
        return self.n_gs_studies_in_scopus_and_bsb_and_fsb / self.gs_size


def preprocess_string(
    string: str,
) -> str:
    r"""Strips the string and turn every character to lower case.

    Args:
        string: The string to preprocess.

    Returns:
        The preprocessed string.

    Examples:
        >>> preprocess_string(" A string Here.  \n")
        'a string here.'
    """
    return string.strip().lower()


def similarity_score(
    *,
    small_set: list[str],
    other_set: list[str],
) -> list[tuple[int, int]]:
    """Uses `TfidfVectorizer`, `cosine_similarity`, and `Levenshtein` to calculate the intersection of two sets of strings.

    You might need to preprocess the strings with [sesg.metrics.preprocess_string][].

    Args:
        small_set (list[str]): Set of strings. If possible, the length of this set should be smaller than the other one.
        other_set (list[str]): Set of strings to compare against.

    Returns:
        List of tuples, where the tuple `(i, j)` means that `small_set[i]` is similar to `other_set[j]`.

    Examples:
        >>> small_set = ["machine learning", "databases", "search strings"]
        >>> other_set = ["Databases, an introduction", "Machine Learning", "Search String"]
        >>> similarity_score(
        ...     small_set=[preprocess_string(string=s) for s in small_set],
        ...     other_set=[preprocess_string(string=s) for s in other_set]
        ... )
        [(0, 1), (2, 2)]
    """  # noqa: E501
    from numpy import argsort
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    # without this "Any typings", pylance takes too long to analyze the sklearn files
    # remove this line once sklearn has developed stubs for the package
    TfidfVectorizer: Any
    cosine_similarity: Any

    if len(other_set) == 0:
        return []

    train_set = [*small_set, *other_set]

    tfidf_vectorizer = TfidfVectorizer()
    tfidf_matrix = tfidf_vectorizer.fit_transform(train_set)

    first_set_matrix = tfidf_matrix[0 : len(small_set)]
    second_set_matrix = tfidf_matrix[len(small_set) : len(small_set) + len(other_set)]

    similarity_matrix = cosine_similarity(
        first_set_matrix,
        second_set_matrix,
    )

    lines: int
    lines, _ = similarity_matrix.shape

    similars: list[tuple[int, int]] = []

    for index_of_first_set_element in range(lines):
        # contains the row of the similarity matrix for the current element
        line = similarity_matrix[index_of_first_set_element]

        index_of_closest_element_in_second_set: int = argsort(line)[-1]

        first_set_element = small_set[index_of_first_set_element]
        second_set_element = other_set[index_of_closest_element_in_second_set]

        distance = Levenshtein.distance(
            first_set_element,
            second_set_element,
            score_cutoff=10,
        )

        if distance < 10:
            similars.append(
                (index_of_first_set_element, index_of_closest_element_in_second_set)
            )

    return similars
