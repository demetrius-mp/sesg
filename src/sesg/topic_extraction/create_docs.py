"""Prepare documents for topic extraction."""

from typing import TypedDict


class DocStudy(TypedDict):
    """Data container for a study that will be used to generate a doc.

    Attributes:
        title (str): Title of the study.
        abstract (str): Abstract of the study.
        keywords (str): Keywords of the study.

    Examples:
        >>> study: DocStudy = {
        ...     "title": "machine learning",
        ...     "abstract": "machine learning is often used in the industry with the goal of...",
        ...     "keywords": "machine learning, code smells, defect detection"
        ... }
        >>> study
        {'title': 'machine learning', 'abstract': 'machine learning is often used in the industry with the goal of...', 'keywords': 'machine learning, code smells, defect detection'}
    """  # noqa: E501

    title: str
    abstract: str
    keywords: str


def concat_study_info(
    study: DocStudy,
) -> str:
    r"""Concatenates the information of the study into a string.

    Args:
        study (DocStudy): Study with title, abstract and keywords.

    Returns:
        A string with the following format: "{title}\n{abstract}\n{keywords}".

    Examples:
        >>> study: DocStudy = {
        ...     "title": "machine learning",
        ...     "abstract": "machine learning is often used in the industry with the goal of...",
        ...     "keywords": "machine learning, code smells, defect detection"
        ... }
        >>> concat_study_info(study)
        'machine learning\nmachine learning is often used in the industry with the goal of...\nmachine learning, code smells, defect detection'
    """  # noqa: E501
    title = study["title"]
    abstract = study["abstract"]
    keywords = study["keywords"]

    return f"{title}\n{abstract}\n{keywords}"


def create_docs(
    studies_list: list[DocStudy],
) -> list[str]:
    r"""Creates a list of documents where each document is a string with the title, abstract and keywords of the study.

    Can be used with [extract_topics_with_lda][sesg.topic_extraction.extract_topics_with_lda] or [extract_topics_with_bertopic][sesg.topic_extraction.extract_topics_with_bertopic].

    Args:
        studies_list (list[DocStudy]): List of studies with title, abstract and keywords.

    Returns:
        List of documents.

    Examples:
        >>> s1: DocStudy = {
        ...     "title": "machine learning",
        ...     "abstract": "machine learning is often used in the industry with the goal of...",
        ...     "keywords": "machine learning, code smells, defect detection"
        ... }
        >>> s2: DocStudy = {
        ...     "title": "artificial intelligence",
        ...     "abstract": "artificial intelligence is often used in the industry with the goal of...",
        ...     "keywords": "artificial intelligence, code smells, defect detection"
        ... }
        >>> create_docs([s1, s2])
        ['machine learning\nmachine learning is often used in the industry with the goal of...\nmachine learning, code smells, defect detection', 'artificial intelligence\nartificial intelligence is often used in the industry with the goal of...\nartificial intelligence, code smells, defect detection']
    """  # noqa: E501
    return [concat_study_info(s) for s in studies_list]
