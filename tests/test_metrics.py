import pytest
from sesg import metrics


@pytest.mark.parametrize(
    "n_scopus_results, expected",
    [
        (10, 10),
        (2_500, 2_500),
        (5_000, 5_000),
        (7_000, 5_000),
    ],
)
def test_metrics_n_scopus_results_with_limit(
    n_scopus_results,
    expected,
):
    metric = metrics.Metrics(
        gs_size=-1,
        n_qgs_studies_in_scopus=-1,
        n_gs_studies_in_scopus=-1,
        n_gs_studies_in_scopus_and_bsb=-1,
        n_gs_studies_in_scopus_and_bsb_and_fsb=-1,
        n_scopus_results=n_scopus_results,
    )

    assert metric.n_scopus_results_with_limit == expected


@pytest.mark.parametrize(
    "n_gs_studies_in_scopus,n_scopus_results,expected",
    [
        (0, 0, 0),
        (25, 100, 25 / 100),
        (25, 5000, 25 / 5_000),
        (25, 10000, 25 / 5_000),
    ],
)
def test_metrics_scopus_precision(
    n_gs_studies_in_scopus,
    n_scopus_results,
    expected,
):
    metric = metrics.Metrics(
        gs_size=-1,
        n_qgs_studies_in_scopus=-1,
        n_gs_studies_in_scopus=n_gs_studies_in_scopus,
        n_gs_studies_in_scopus_and_bsb=-1,
        n_gs_studies_in_scopus_and_bsb_and_fsb=-1,
        n_scopus_results=n_scopus_results,
    )

    assert metric.scopus_precision == expected


@pytest.mark.parametrize(
    "n_gs_studies_in_scopus,gs_size,expected",
    [
        (0, 30, 0),
        (10, 30, 10 / 30),
        (21, 30, 21 / 30),
        (30, 30, 1),
    ],
)
def test_metrics_scopus_recall(
    n_gs_studies_in_scopus,
    gs_size,
    expected,
):
    metric = metrics.Metrics(
        gs_size=gs_size,
        n_qgs_studies_in_scopus=-1,
        n_gs_studies_in_scopus=n_gs_studies_in_scopus,
        n_gs_studies_in_scopus_and_bsb=-1,
        n_gs_studies_in_scopus_and_bsb_and_fsb=-1,
        n_scopus_results=-1,
    )

    assert metric.scopus_recall == expected


@pytest.mark.parametrize(
    "n_gs_studies_in_scopus,n_scopus_results,gs_size,expected",
    [
        (0, 0, 30, 0),
        (25, 100, 30, 0.3846153846153846),
        (0, 100, 30, 0),
    ],
)
def test_metrics_scopus_f1_score(
    n_gs_studies_in_scopus,
    n_scopus_results,
    gs_size,
    expected,
):
    metric = metrics.Metrics(
        gs_size=gs_size,
        n_qgs_studies_in_scopus=-1,
        n_gs_studies_in_scopus=n_gs_studies_in_scopus,
        n_gs_studies_in_scopus_and_bsb=-1,
        n_gs_studies_in_scopus_and_bsb_and_fsb=-1,
        n_scopus_results=n_scopus_results,
    )

    assert metric.scopus_f1_score == pytest.approx(expected)


@pytest.mark.parametrize(
    "n_gs_studies_in_scopus_and_bsb,gs_size,expected",
    [
        (0, 30, 0),
        (15, 30, 15 / 30),
        (30, 30, 1),
    ],
)
def test_metrics_scopus_and_bsb_recall(
    n_gs_studies_in_scopus_and_bsb,
    gs_size,
    expected,
):
    metric = metrics.Metrics(
        gs_size=gs_size,
        n_qgs_studies_in_scopus=-1,
        n_gs_studies_in_scopus=-1,
        n_gs_studies_in_scopus_and_bsb=n_gs_studies_in_scopus_and_bsb,
        n_gs_studies_in_scopus_and_bsb_and_fsb=-1,
        n_scopus_results=-1,
    )

    assert metric.scopus_and_bsb_recall == pytest.approx(expected)


@pytest.mark.parametrize(
    "n_gs_studies_in_scopus_and_bsb_and_fsb,gs_size,expected",
    [
        (0, 30, 0),
        (15, 30, 15 / 30),
        (30, 30, 1),
    ],
)
def test_metrics_scopus_and_bsb_and_fsb_recall(
    n_gs_studies_in_scopus_and_bsb_and_fsb,
    gs_size,
    expected,
):
    metric = metrics.Metrics(
        gs_size=gs_size,
        n_qgs_studies_in_scopus=-1,
        n_gs_studies_in_scopus=-1,
        n_gs_studies_in_scopus_and_bsb=-1,
        n_gs_studies_in_scopus_and_bsb_and_fsb=n_gs_studies_in_scopus_and_bsb_and_fsb,
        n_scopus_results=-1,
    )

    assert metric.scopus_and_bsb_and_fsb_recall == pytest.approx(expected)


def test_preprocess_string_should_strip_and_turn_to_lowercase():
    value = "  leading whitespace UPPERCASE  "
    expected = "leading whitespace uppercase"

    result = metrics.preprocess_string(value)

    assert expected == result


def test_preprocess_string_should_keep_special_characters():
    value = "  leading whitespace UPPERCASE"
    special_characters = "string,<>;:/?~^'`[{()}]!@#$%&*-_=+'\""
    expected = "leading whitespace uppercase" + special_characters

    result = metrics.preprocess_string(value + special_characters + "  ")

    assert expected == result


def test_similarity_score_should_return_empty_array_when_sets_are_empty():
    result = metrics.similarity_score(
        small_set=[],
        other_set=[],
    )
    expected = []

    assert result == expected
