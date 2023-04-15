from typing import List, Optional

from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    Integer,
    Table,
    Text,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


def todict(obj):
    """Return the object's dict excluding private attributes,
    sqlalchemy state and relationship attributes.
    """
    excl = ("_sa_adapter", "_sa_instance_state")
    return {
        k: v
        for k, v in vars(obj).items()
        if not k.startswith("_") and not any(hasattr(v, a) for a in excl)
    }


class Base(DeclarativeBase):
    def __repr__(self):
        params = ", ".join(f"{k}={v}" for k, v in todict(self).items())
        return f"{self.__class__.__name__}({params})"


experiments_studies_association_table = Table(
    "experiments_studies_association_table",
    Base.metadata,
    Column("experiment_id", ForeignKey("experiment.id"), primary_key=True),
    Column("study_id", ForeignKey("study.id"), primary_key=True),
)

metric_qgs_studies_in_scopus_association_table = Table(
    "metric_qgs_studies_in_scopus_association_table",
    Base.metadata,
    Column("metric_id", ForeignKey("metric.id"), primary_key=True),
    Column("study_id", ForeignKey("study.id"), primary_key=True),
)

metric_gs_studies_in_scopus_association_table = Table(
    "metric_gs_studies_in_scopus_association_table",
    Base.metadata,
    Column("metric_id", ForeignKey("metric.id"), primary_key=True),
    Column("study_id", ForeignKey("study.id"), primary_key=True),
)

metric_gs_studies_in_scopus_and_bsb_association_table = Table(
    "metric_gs_studies_in_scopus_and_bsb_association_table",
    Base.metadata,
    Column("metric_id", ForeignKey("metric.id"), primary_key=True),
    Column("study_id", ForeignKey("study.id"), primary_key=True),
)

metric_gs_studies_in_scopus_and_bsb_and_fsb_association_table = Table(
    "metric_gs_studies_in_scopus_and_bsb_and_fsb_association_table",
    Base.metadata,
    Column("metric_id", ForeignKey("metric.id"), primary_key=True),
    Column("study_id", ForeignKey("study.id"), primary_key=True),
)

study_citations_association_table = Table(
    "study_citations_association_table",
    Base.metadata,
    Column("study_id", ForeignKey("study.id"), primary_key=True),
    Column("reference_id", ForeignKey("study.id"), primary_key=True),
)


class SLR(Base):
    __tablename__ = "slr"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(Text(), unique=True)
    min_publication_year: Mapped[Optional[int]]
    max_publication_year: Mapped[Optional[int]]

    gs_studies: Mapped[List["Study"]] = relationship(
        back_populates="slr",
    )

    experiments: Mapped[List["Experiment"]] = relationship(
        back_populates="slr",
    )


class Study(Base):
    __tablename__ = "study"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(Text())
    abstract: Mapped[str] = mapped_column(Text())
    keywords: Mapped[str] = mapped_column(Text())

    references: Mapped[List["Study"]] = relationship(
        secondary=study_citations_association_table,
        primaryjoin=id == study_citations_association_table.c.study_id,
        secondaryjoin=id == study_citations_association_table.c.reference_id,
        backref="cited_by",
    )

    slr_id: Mapped[int] = mapped_column(ForeignKey("slr.id"))
    slr: Mapped["SLR"] = relationship(
        back_populates="gs_studies",
    )

    experiments: Mapped[List["Experiment"]] = relationship(
        secondary=experiments_studies_association_table,
        back_populates="qgs_studies",
    )


class Experiment(Base):
    __tablename__ = "experiment"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text(), unique=True)

    slr_id: Mapped[int] = mapped_column(ForeignKey("slr.id"))
    slr: Mapped["SLR"] = relationship(
        back_populates="experiments",
    )

    qgs_studies: Mapped[List["Study"]] = relationship(
        secondary=experiments_studies_association_table,
        back_populates="experiments",
    )

    list_of_lda_parameters: Mapped[List["LDAParameters"]] = relationship(
        back_populates="experiment",
    )
    list_of_bertopic_parameters: Mapped[List["BERTopicParameters"]] = relationship(
        back_populates="experiment"
    )


class LDAParameters(Base):
    __tablename__ = "lda_parameters"

    id: Mapped[int] = mapped_column(primary_key=True)

    min_document_frequency: Mapped[float] = mapped_column(Float())
    number_of_topics: Mapped[int] = mapped_column(Integer())

    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiment.id"))
    experiment: Mapped["Experiment"] = relationship(
        back_populates="list_of_lda_parameters",
    )

    topics: Mapped[List["Topic"]] = relationship(
        back_populates="lda_parameters",
    )

    search_string: Mapped["SearchString"] = relationship(
        back_populates="lda_parameters",
    )


class BERTopicParameters(Base):
    __tablename__ = "bertopic_parameters"

    id: Mapped[int] = mapped_column(primary_key=True)

    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiment.id"))
    experiment: Mapped["Experiment"] = relationship(
        back_populates="list_of_bertopic_parameters",
    )

    topics: Mapped[List["Topic"]] = relationship(
        back_populates="bertopic_parameters",
    )

    search_string: Mapped["SearchString"] = relationship(
        back_populates="bertopic_parameters",
    )


class Topic(Base):
    __tablename__ = "topic"

    id: Mapped[int] = mapped_column(primary_key=True)

    words: Mapped[List["TopicWord"]] = relationship(
        back_populates="topic",
    )

    lda_parameters_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("lda_parameters.id")
    )
    lda_parameters: Mapped[Optional["LDAParameters"]] = relationship(
        back_populates="topics",
    )

    bertopic_parameters_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("bertopic_parameters.id")
    )
    bertopic_parameters: Mapped[Optional["BERTopicParameters"]] = relationship(
        back_populates="topics",
    )


class TopicWord(Base):
    __tablename__ = "topic_word"

    id: Mapped[int] = mapped_column(primary_key=True)
    word: Mapped[str] = mapped_column(Text())

    topic_id: Mapped[int] = mapped_column(ForeignKey("topic.id"))
    topic: Mapped["Topic"] = relationship(
        back_populates="words",
    )


class SearchString(Base):
    __tablename__ = "search_string"

    id: Mapped[int] = mapped_column(primary_key=True)
    string: Mapped[str] = mapped_column(Text())

    number_of_words_per_topic: Mapped[int] = mapped_column(Integer())
    number_of_similar_words: Mapped[int] = mapped_column(Integer())

    lda_parameters_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("lda_parameters.id")
    )
    lda_parameters: Mapped[Optional["LDAParameters"]] = relationship(
        back_populates="search_string",
    )

    bertopic_parameters_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("bertopic_parameters.id")
    )
    bertopic_parameters: Mapped[Optional["BERTopicParameters"]] = relationship(
        back_populates="search_string",
    )

    metric: Mapped["Metric"] = relationship(
        back_populates="search_string",
    )

    scopus_result: Mapped["ScopusResult"] = relationship(
        back_populates="search_string",
    )


class ScopusResult(Base):
    __tablename__ = "scopus_result"

    id: Mapped[int] = mapped_column(primary_key=True)

    compressed_titles: Mapped[bytes]

    search_string_id: Mapped[int] = mapped_column(
        ForeignKey("search_string.id"),
        unique=True,
    )
    search_string: Mapped["SearchString"] = relationship(
        back_populates="scopus_result",
    )


class Metric(Base):
    __tablename__ = "metric"

    id: Mapped[int] = mapped_column(primary_key=True)

    qgs_studies_in_scopus: Mapped[List["Study"]] = relationship(
        secondary=metric_qgs_studies_in_scopus_association_table,
    )

    gs_studies_in_scopus: Mapped[List["Study"]] = relationship(
        secondary=metric_gs_studies_in_scopus_association_table,
    )

    gs_studies_in_scopus_and_bsb: Mapped[List["Study"]] = relationship(
        secondary=metric_gs_studies_in_scopus_and_bsb_association_table,
    )

    gs_studies_in_scopus_and_bsb_and_fsb: Mapped[List["Study"]] = relationship(
        secondary=metric_gs_studies_in_scopus_and_bsb_and_fsb_association_table,
    )

    n_scopus_results: Mapped[int] = mapped_column(Integer())
    n_qgs_studies_in_scopus: Mapped[int]
    n_gs_studies_in_scopus: Mapped[int]
    n_gs_studies_in_scopus_and_bsb: Mapped[int]
    n_gs_studies_in_scopus_and_bsb_and_fsb: Mapped[int]

    scopus_precision: Mapped[float] = mapped_column(Float())
    scopus_recall: Mapped[float] = mapped_column(Float())
    scopus_f1_score: Mapped[float] = mapped_column(Float())

    scopus_and_bsb_recall: Mapped[float] = mapped_column(Float())
    scopus_and_bsb_and_fsb_recall: Mapped[float] = mapped_column(Float())

    search_string_id: Mapped[int] = mapped_column(
        ForeignKey("search_string.id"),
        unique=True,
    )
    search_string: Mapped["SearchString"] = relationship(
        back_populates="metric",
    )
