import pytest
from sesg.evaluation.evaluation_factory import (
    Evaluation,
    EvaluationFactory,
    Study,
    get_directed_adjacency_list_from_gs,
    process_title,
    similarity_score,
)


def test_similarity_score():
    small_set = ["machine learning", "databases", "search strings"]
    other_set = ["Databases, an introduction", "Machine Learning", "Search String"]
    expected_result = [(0, 1), (2, 2)]

    preprocessed_small_set = [process_title(s) for s in small_set]
    preprocessed_other_set = [process_title(s) for s in other_set]

    result = similarity_score(preprocessed_small_set, preprocessed_other_set)
    assert result == expected_result


def test_similarity_score_empty_sets():
    small_set = []
    other_set = []
    expected_result = []

    result = similarity_score(small_set, other_set)
    assert result == expected_result


def test_similarity_score_single_set():
    small_set = ["machine learning"]
    other_set = ["Databases, an introduction", "Machine Learning", "Search String"]
    expected_result = [(0, 1)]

    preprocessed_small_set = [process_title(s) for s in small_set]
    preprocessed_other_set = [process_title(s) for s in other_set]

    result = similarity_score(preprocessed_small_set, preprocessed_other_set)
    assert result == expected_result


def test_process_title():
    string = " A string Here.  \n"
    expected_result = "a string here."

    assert process_title(string) == expected_result


def test_process_title_empty_string():
    string = ""
    expected_result = ""

    assert process_title(string) == expected_result


def test_process_title_whitespace_string():
    string = "   "
    expected_result = ""

    assert process_title(string) == expected_result


def test_get_directed_adjacency_list_from_gs():
    study1 = Study(id=1, title="Study 1")
    study2 = Study(id=2, title="Study 2")
    study3 = Study(id=3, title="Study 3")

    study2.references.append(study1)
    study3.references.append(study2)

    gs = [study1, study2, study3]

    adjacency_list = get_directed_adjacency_list_from_gs(gs)

    expected_adjacency_list = {
        1: [],
        2: [1],
        3: [2],
    }

    assert adjacency_list == expected_adjacency_list


def test_study_processed_title():
    study = Study(1, " A Study Title ")
    expected_result = "a study title"

    assert study.processed_title == expected_result


def test_study_processed_title_empty():
    study = Study(1, "")
    expected_result = ""

    assert study.processed_title == expected_result


def test_study_references_default_factory():
    study = Study(1, "Study 1")
    assert study.references == []


def test_study_references():
    study1 = Study(1, "Study 1")
    study2 = Study(2, "Study 2")
    study3 = Study(3, "Study 3")

    study1.references = [study2, study3]
    assert study1.references == [study2, study3]


def test_evaluation_start_set_precision_should_return_0_when_n_scopus_results_is_0():
    evaluation = Evaluation(
        gs_size=15,
        n_scopus_results=0,
    )

    assert evaluation.start_set_precision == 0


def mock_study_list(n: int) -> list[Study]:
    return [Study(1, "Study")] * n


@pytest.mark.parametrize(
    "gs_in_scopus, n_scopus_results, expected_start_set_precision",
    [
        (mock_study_list(3), 150, 0.02),
        (mock_study_list(18), 300, 0.06),
    ],
)
def test_evaluation_start_set_precision(
    gs_in_scopus,
    n_scopus_results,
    expected_start_set_precision,
):
    evaluation = Evaluation(
        gs_size=-1,
        n_scopus_results=n_scopus_results,
        gs_in_scopus=gs_in_scopus,
    )

    assert evaluation.start_set_precision == expected_start_set_precision


@pytest.mark.parametrize(
    "gs_in_scopus, gs_size, expected_start_set_recall",
    [
        (mock_study_list(3), 15, 0.2),
        (mock_study_list(9), 15, 0.6),
    ],
)
def test_evaluation_start_set_recall(
    gs_in_scopus,
    gs_size,
    expected_start_set_recall,
):
    evaluation = Evaluation(
        n_scopus_results=-1,
        gs_size=gs_size,
        gs_in_scopus=gs_in_scopus,
    )

    assert evaluation.start_set_recall == expected_start_set_recall


def test_evaluation_start_set_f1_score_should_return_0_when_start_set_precision_and_start_set_recall_are_0():
    evaluation = Evaluation(
        n_scopus_results=0,
        gs_in_scopus=[],
        gs_size=15,
    )

    assert evaluation.start_set_f1_score == 0


@pytest.mark.parametrize(
    "gs_in_scopus, gs_size, n_scopus_results, expected_start_set_f1_score",
    [
        (mock_study_list(2), 20, 200, 0.018181818),
        (mock_study_list(4), 25, 250, 0.029090909),
    ],
)
def test_evaluation_start_set_f1_score(
    gs_in_scopus,
    gs_size,
    n_scopus_results,
    expected_start_set_f1_score,
):
    evaluation = Evaluation(
        n_scopus_results=n_scopus_results,
        gs_size=gs_size,
        gs_in_scopus=gs_in_scopus,
    )

    assert evaluation.start_set_f1_score == pytest.approx(expected_start_set_f1_score)


@pytest.mark.parametrize(
    "gs_in_bsb, gs_size, expected_bsb_recall",
    [
        (mock_study_list(3), 15, 0.2),
        (mock_study_list(9), 15, 0.6),
    ],
)
def test_evaluation_bsb_recall(
    gs_in_bsb,
    gs_size,
    expected_bsb_recall,
):
    evaluation = Evaluation(
        n_scopus_results=-1,
        gs_size=gs_size,
        gs_in_bsb=gs_in_bsb,
    )

    assert evaluation.bsb_recall == expected_bsb_recall


@pytest.mark.parametrize(
    "gs_in_sb, gs_size, expected_sb_recall",
    [
        (mock_study_list(3), 15, 0.2),
        (mock_study_list(9), 15, 0.6),
    ],
)
def test_evaluation_sb_recall(
    gs_in_sb,
    gs_size,
    expected_sb_recall,
):
    evaluation = Evaluation(
        n_scopus_results=-1,
        gs_size=gs_size,
        gs_in_sb=gs_in_sb,
    )

    assert evaluation.sb_recall == expected_sb_recall


@pytest.fixture()
def gs():
    study1 = Study(1, "Machine learning")
    study2 = Study(2, "Deep learning")
    study3 = Study(3, "Artificial intelligence")
    study4 = Study(4, "Natural language processing")
    study5 = Study(5, "Computer vision")

    study4.references = [study1]
    study5.references = [study1, study2, study3]

    return [study1, study2, study3, study4, study5]


@pytest.fixture()
def qgs(gs: list[Study]):
    study3 = gs[2]
    study4 = gs[3]

    return [study3, study4]


def test_evaluation_factory(gs: list[Study], qgs: list[Study]):
    evaluation_factory = EvaluationFactory(
        gs=gs,
        qgs=qgs,
    )

    result = evaluation_factory.evaluate(
        ["machine learning", "natural language processing", *["random string"] * 198]
    )

    expected = Evaluation(
        n_scopus_results=200,
        gs_size=5,
        qgs_in_scopus=[gs[3]],
        gs_in_scopus=[gs[0], gs[1], gs[3]],
        gs_in_bsb=[gs[0], gs[1], gs[3]],
        gs_in_sb=gs,
    )

    assert result == expected
