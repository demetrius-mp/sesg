from typing import (
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    TypedDict,
    Union,
)

from sesg.topic_extraction import TopicExtractionStrategy
from sqlalchemy import insert, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from . import models as m


class StudyData(TypedDict):
    title: str
    abstract: str
    keywords: str


class LDAEntry(TypedDict):
    min_document_frequency: float
    number_of_topics: int
    topics: Iterable[Iterable[str]]


class BERTopicEntry(TypedDict):
    topics: Iterable[Iterable[str]]


class SearchStringData(TypedDict):
    string: str
    number_of_words_per_topic: int
    number_of_similar_words: int
    lda_parameters_id: Optional[int]
    bertopic_parameters_id: Optional[int]


class MetricData(TypedDict):
    search_string_id: int

    n_scopus_results: int

    qgs_studies_in_scopus: Sequence[int]
    gs_studies_in_scopus: Sequence[int]
    gs_studies_in_scopus_and_bsb: Sequence[int]
    gs_studies_in_scopus_and_bsb_and_fsb: Sequence[int]

    scopus_precision: float
    scopus_recall: float
    scopus_f1_score: float

    scopus_and_bsb_recall: float
    scopus_and_bsb_and_fsb_recall: float


def create_slr(
    name: str,
    session: Session,
    min_publication_year: Optional[int] = None,
    max_publication_year: Optional[int] = None,
):
    entity = m.SLR(
        name=name,
        min_publication_year=min_publication_year,
        max_publication_year=max_publication_year,
    )

    session.add(entity)
    session.commit()
    session.refresh(entity)

    return entity


def get_slr_by_name(
    name: str,
    session: Session,
):
    stmt = select(m.SLR).where(m.SLR.name == name)
    slr = session.execute(stmt).scalar_one()

    return slr


def add_many_studies_to_slr(
    slr_id: int,
    studies: Iterable[StudyData],
    session: Session,
):
    entities: List[m.Study] = []
    for data in studies:
        study = m.Study(
            title=data["title"],
            abstract=data["abstract"],
            keywords=data["keywords"],
            slr_id=slr_id,
        )

        entities.append(study)

    stmt = select(m.Study).where(m.Study.slr_id == slr_id).order_by(m.Study.id)

    session.add_all(entities)
    session.commit()

    refreshed_entities = session.execute(stmt).scalars().all()

    return refreshed_entities


def add_study_references(
    slr_gs_studies: List[m.Study],
    study_id: int,
    references: Iterable[int],
    session: Session,
):
    if len(slr_gs_studies) == 0:
        raise RuntimeError("This SLR does not have any study.")

    gs_studies_ids = [s.id for s in slr_gs_studies]

    study_is_in_gs = study_id in gs_studies_ids

    if not study_is_in_gs:
        raise RuntimeError(f"Study with id {study_id} is not on the GS.")

    if not all(ref in gs_studies_ids for ref in references):
        raise RuntimeError("One of the references is not on the GS.")

    values = [
        {"study_id": study_id, "reference_id": reference_id}
        for reference_id in references
    ]

    stmt = insert(m.study_citations_association_table).values(values)

    session.execute(stmt)
    session.commit()


def get_slr_citation_edges(
    slr_id: int,
    session: Session,
):
    stmt = select(m.Study).where(m.Study.slr_id == slr_id).order_by(m.Study.id)
    edges: List[Tuple[int, int]] = list()

    studies = session.execute(stmt).scalars().all()

    if len(studies) == 0:
        raise RuntimeError("This SLR does not have any study.")

    for s in studies:
        s_edges = [(s.id, ref.id) for ref in s.references]

        edges.extend(s_edges)

    return edges


def create_experiment(
    slr_id: int,
    slr_gs_studies: List[m.Study],
    experiment_name: str,
    qgs_studies: List[m.Study],
    session: Session,
):
    gs_studies_ids = [s.id for s in slr_gs_studies]

    if len(slr_gs_studies) == 0:
        raise RuntimeError("This SLR does not have any study.")

    entity = m.Experiment(
        name=experiment_name,
        slr_id=slr_id,
    )

    if not all(s.id in gs_studies_ids for s in qgs_studies):
        raise RuntimeError("One of the studies is not on the GS.")

    entity.qgs_studies = qgs_studies

    session.add(entity)
    session.commit()
    session.refresh(entity)

    return entity


def get_experiment_by_name(
    slr_id: int,
    experiment_name: str,
    session: Session,
):
    stmt = (
        select(m.Experiment)
        .where(m.Experiment.slr_id == slr_id)
        .where(m.Experiment.name == experiment_name)
    )

    experiment = session.execute(stmt).scalar_one()

    return experiment


def get_many_lda_parameters_by_experiment(
    session: Session,
    experiment_id: int,
):
    stmt = (
        select(m.LDAParameters)
        .where(m.LDAParameters.experiment_id == experiment_id)
        .order_by(m.LDAParameters.id)
    )

    parameters = session.execute(stmt).scalars().all()

    return parameters


def get_many_bertopic_parameters_by_experiment(
    session: Session,
    experiment_id: int,
):
    stmt = (
        select(m.BERTopicParameters)
        .where(m.BERTopicParameters.experiment_id == experiment_id)
        .order_by(m.BERTopicParameters.id)
    )

    parameters = session.execute(stmt).scalars().all()

    return parameters


def create_many_bertopic_entries(
    experiment_id: int,
    entries: Iterable[BERTopicEntry],
    session: Session,
):
    instances: Sequence[m.BERTopicParameters] = list()
    for entry in entries:
        instance = m.BERTopicParameters(
            experiment_id=experiment_id,
        )

        topics_instances: Sequence[m.Topic] = list()
        for topic in entry["topics"]:
            topic_instance = m.Topic()

            words_instances = [m.TopicWord(word=word) for word in topic]
            topic_instance.words = words_instances

            topics_instances.append(topic_instance)

        instance.topics = topics_instances
        instances.append(instance)

    session.add_all(instances)
    session.commit()


def create_many_lda_entries(
    experiment_id: int,
    entries: Iterable[LDAEntry],
    session: Session,
):
    instances: Sequence[m.LDAParameters] = list()
    for entry in entries:
        instance = m.LDAParameters(
            experiment_id=experiment_id,
            min_document_frequency=entry["min_document_frequency"],
            number_of_topics=entry["number_of_topics"],
        )

        topics_instances: Sequence[m.Topic] = list()
        for topic in entry["topics"]:
            topic_instance = m.Topic()

            words_instances = [m.TopicWord(word=word) for word in topic]
            topic_instance.words = words_instances

            topics_instances.append(topic_instance)

        instance.topics = topics_instances
        instances.append(instance)

    session.add_all(instances)
    session.commit()


def create_many_search_strings(
    search_strings: Iterable[SearchStringData],
    session: Session,
):
    entities = [
        m.SearchString(
            string=s["string"],
            number_of_words_per_topic=s["number_of_words_per_topic"],
            number_of_similar_words=s["number_of_similar_words"],
            lda_parameters_id=s["lda_parameters_id"],
            bertopic_parameters_id=s["bertopic_parameters_id"],
        )
        for s in search_strings
    ]

    session.add_all(entities)
    session.commit()


def get_last_used_search_string_id(
    experiment_id: int,
    topic_extraction_strategy: TopicExtractionStrategy,
    session: Session,
) -> Union[int, None]:
    stmt = select(func.max(m.ScopusResult.search_string_id)).join(
        m.ScopusResult.search_string
    )

    if topic_extraction_strategy.value == TopicExtractionStrategy.bertopic:
        stmt = stmt.join(m.SearchString.bertopic_parameters).join(
            m.BERTopicParameters.experiment
        )

    elif topic_extraction_strategy.value == TopicExtractionStrategy.lda:
        stmt = stmt.join(m.SearchString.lda_parameters).join(m.LDAParameters.experiment)

    else:
        raise RuntimeError("Invalid topic extraction strategy")

    stmt = stmt.where(m.Experiment.id == experiment_id)

    last_used_search_string = session.execute(stmt).scalar()

    return last_used_search_string


def get_search_string_by_id(
    search_string_id: int,
    session: Session,
):
    stmt = select(m.SearchString).where(m.SearchString.id == search_string_id)

    return session.execute(stmt).scalar_one()


def get_many_search_strings(
    experiment_id: int,
    session: Session,
    topic_extraction_strategy: TopicExtractionStrategy,
):
    stmt = select(m.SearchString)

    if topic_extraction_strategy.value == TopicExtractionStrategy.bertopic:
        stmt = stmt.join(m.SearchString.bertopic_parameters).join(
            m.BERTopicParameters.experiment
        )

    elif topic_extraction_strategy.value == TopicExtractionStrategy.lda:
        stmt = stmt.join(m.SearchString.lda_parameters).join(m.LDAParameters.experiment)

    else:
        raise RuntimeError("Invalid topic extraction strategy")

    stmt = stmt.where(m.Experiment.id == experiment_id)

    stmt = stmt.order_by(m.SearchString.id)

    search_strings = session.execute(stmt).scalars().all()

    return search_strings


def create_scopus_result(
    search_string_id: int,
    compressed_titles: bytes,
    session: Session,
):
    entity = m.ScopusResult(
        compressed_titles=compressed_titles,
        search_string_id=search_string_id,
    )

    session.add(entity)
    session.commit()


def get_many_scopus_results_by_search_string(
    search_string_id: int,
    session: Session,
):
    stmt = (
        select(m.ScopusResult)
        .where(m.ScopusResult.search_string_id == search_string_id)
        .order_by(m.ScopusResult.id)
    )

    scopus_results = session.execute(stmt).scalars().all()

    return scopus_results


def create_many_metrics(
    gs_studies: Sequence[m.Study],
    metrics: Sequence[MetricData],
    session: Session,
):
    gs_studies_map: Mapping[int, m.Study] = {s.id: s for s in gs_studies}

    metric_instances: List[m.Metric] = list()
    for metric in metrics:
        metric_instance = m.Metric(
            scopus_precision=metric["scopus_precision"],
            scopus_recall=metric["scopus_recall"],
            scopus_f1_score=metric["scopus_f1_score"],
            scopus_and_bsb_recall=metric["scopus_and_bsb_recall"],
            scopus_and_bsb_and_fsb_recall=metric["scopus_and_bsb_and_fsb_recall"],
            search_string_id=metric["search_string_id"],
            n_scopus_results=metric["n_scopus_results"],
            n_qgs_studies_in_scopus=len(metric["qgs_studies_in_scopus"]),
            n_gs_studies_in_scopus=len(metric["gs_studies_in_scopus"]),
            n_gs_studies_in_scopus_and_bsb=len(metric["gs_studies_in_scopus_and_bsb"]),
            n_gs_studies_in_scopus_and_bsb_and_fsb=len(
                metric["gs_studies_in_scopus_and_bsb_and_fsb"]
            ),
        )

        metric_instance.qgs_studies_in_scopus = [
            gs_studies_map[study_id] for study_id in metric["qgs_studies_in_scopus"]
        ]

        metric_instance.gs_studies_in_scopus = [
            gs_studies_map[study_id] for study_id in metric["gs_studies_in_scopus"]
        ]

        metric_instance.gs_studies_in_scopus_and_bsb = [
            gs_studies_map[study_id]
            for study_id in metric["gs_studies_in_scopus_and_bsb"]
        ]

        metric_instance.gs_studies_in_scopus_and_bsb_and_fsb = [
            gs_studies_map[study_id]
            for study_id in metric["gs_studies_in_scopus_and_bsb_and_fsb"]
        ]

        metric_instances.append(metric_instance)

    session.add_all(metric_instances)
    session.commit()


if __name__ == "__main__":
    ...
