from pathlib import Path
from typing import List

import typer
from rich import print
from rich.progress import Progress

from experiment.database import queries as db
from experiment.database.core import Session
from experiment.settings import get_settings


app = typer.Typer(rich_markup_mode="markdown")


@app.command()
def with_bertopic(
    slr_name: str = typer.Argument(
        ...,
        help="Name of the Systematic Literature Review",
    ),
    experiment_name: str = typer.Argument(
        ...,
        help="Name of the Experiment",
    ),
):
    from sesg.topic_extraction import extract_topics_with_bertopic

    with Session() as session:
        slr = db.get_slr_by_name(
            name=slr_name,
            session=session,
        )
        experiment = db.get_experiment_by_name(
            slr_id=slr.id,
            experiment_name=experiment_name,
            session=session,
        )
        qgs_studies = experiment.qgs_studies

    docs = [f"{s.title}\n{s.abstract}\n{s.keywords}" for s in qgs_studies]

    # if there are less than 10 documents
    # duplicate the available documents
    if len(docs) < 10:
        print("[blue]Less than 10 documents. Duplicating available documents...")
        docs = [*docs, *docs]

    list_of_parameters = [None]
    list_of_entries: List[db.BERTopicEntry] = list()

    n_variations = len(list_of_parameters)
    with Progress() as progress:
        topic_extraction_progress_task = progress.add_task(
            "[green]Extracting topics...",
            total=n_variations,
        )

        for i, parameters in enumerate(list_of_parameters):
            list_of_topics = extract_topics_with_bertopic(
                docs=docs,
            )

            entry = db.BERTopicEntry(
                topics=list_of_topics,
            )

            list_of_entries.append(entry)

            progress.update(
                topic_extraction_progress_task,
                description=f"[green]Extracting topics ({i + 1} of {n_variations})",
                advance=1,
                refresh=True,
            )

    with Session() as session:
        db.create_many_bertopic_entries(
            experiment_id=experiment.id,
            entries=list_of_entries,
            session=session,
        )


@app.command()
def with_lda(
    slr_name: str = typer.Argument(
        ...,
        help="Name of the Systematic Literature Review",
    ),
    experiment_name: str = typer.Argument(
        ...,
        help="Name of the Experiment",
    ),
    settings_file_path: Path = typer.Option(
        Path.cwd() / "settings.toml",
        "--setings-file-path",
        "-f",
        help="Path to the `settings.toml` file",
    ),
):
    import itertools

    from sesg.topic_extraction import extract_topics_with_lda

    settings = get_settings(
        settings_file_path=settings_file_path,
    )

    min_df_list = settings.lda_parameters.min_document_frequency
    number_topics_list = settings.lda_parameters.number_of_topics

    with Session() as session:
        slr = db.get_slr_by_name(
            name=slr_name,
            session=session,
        )
        experiment = db.get_experiment_by_name(
            slr_id=slr.id,
            experiment_name=experiment_name,
            session=session,
        )
        qgs_studies = experiment.qgs_studies

    docs = [f"{s.title}\n{s.abstract}\n{s.keywords}" for s in qgs_studies]

    list_of_parameters = list(itertools.product(min_df_list, number_topics_list))
    list_of_entries: List[db.LDAEntry] = list()

    n_variations = len(list_of_parameters)

    with Progress() as progress:
        topic_extraction_progress_task = progress.add_task(
            "[green]Extracting topics...",
            total=n_variations,
        )

        for i, (min_document_frequency, number_of_topics) in enumerate(
            list_of_parameters
        ):
            topics = extract_topics_with_lda(
                docs=docs,
                min_document_frequency=min_document_frequency,
                number_of_topics=number_of_topics,
            )

            topics = [words[:10] for words in topics]

            entry = db.LDAEntry(
                min_document_frequency=min_document_frequency,
                number_of_topics=number_of_topics,
                topics=topics,
            )

            list_of_entries.append(entry)

            progress.update(
                topic_extraction_progress_task,
                description=f"[green]Extracting topics ({i + 1} of {n_variations})",
                advance=1,
                refresh=True,
            )

    with Session() as session:
        db.create_many_lda_entries(
            experiment_id=experiment.id,
            entries=list_of_entries,
            session=session,
        )


if __name__ == "__main__":
    app()
