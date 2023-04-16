import itertools
from pathlib import Path
from typing import Any, List

import typer
from rich import print
from rich.progress import Progress
from sesg.topic_extraction import TopicExtractionStrategy

from experiment.config import get_config
from experiment.database import queries as db
from experiment.database.core import Session


app = typer.Typer(rich_markup_mode="markdown")


@app.command()
def generate(
    slr_name: str = typer.Argument(
        ...,
        help="Name of the Systematic Literature Review",
    ),
    experiment_name: str = typer.Argument(
        ...,
        help="Name of the Experiment",
    ),
    topic_extraction_strategy: TopicExtractionStrategy = typer.Option(
        ...,
        "--topic-extraction-strategy",
        "-s",
        case_sensitive=False,
        help="The Topic extraction method that used to generate the search strings that will be used against Scopus.",  # noqa: E501
    ),
    config_file_path: Path = typer.Option(
        Path.cwd() / "config.toml",
        "--config-file-path",
        "-c",
        help="Path to the `config.toml` file.",
    ),
):
    from sesg.search_string import (
        generate_enrichment_text,
        generate_search_string,
    )
    from transformers import BertForMaskedLM, BertTokenizer

    settings = get_config(
        config_file_path=config_file_path,
    )

    print("Querying database...")

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

    enrichment_text = generate_enrichment_text(
        studies_list=[
            {
                "abstract": s.abstract,
                "title": s.title,
            }
            for s in qgs_studies
        ],
    )

    with Session() as session:
        is_lda = topic_extraction_strategy.value == TopicExtractionStrategy.lda
        is_bertopic = (
            topic_extraction_strategy.value == TopicExtractionStrategy.bertopic
        )

        if is_bertopic:
            list_of_model_parameters = db.get_many_bertopic_parameters_by_experiment(
                session=session,
                experiment_id=experiment.id,
            )

        elif is_lda:
            list_of_model_parameters = db.get_many_lda_parameters_by_experiment(
                session=session,
                experiment_id=experiment.id,
            )

        else:
            raise ValueError("Invalid Topic Extraction Strategy.")

        search_strings: List[db.SearchStringData] = list()

        list_of_number_of_words_per_topic = (
            settings.string_formulation_parameters.number_of_words_per_topic
        )
        list_of_number_of_similar_words = (
            settings.string_formulation_parameters.number_of_similar_words
        )

        print("Loading language models...")
        bert_tokenizer: Any = BertTokenizer.from_pretrained("bert-base-uncased")
        bert_model: Any = BertForMaskedLM.from_pretrained("bert-base-uncased")

        bert_model.eval()

        all_parameters = list(
            itertools.product(
                list_of_model_parameters,
                list_of_number_of_words_per_topic,
                list_of_number_of_similar_words,
            )
        )

        n_total_variations = len(all_parameters)
        with Progress() as progress:
            string_generation_progess_task = progress.add_task(
                "[green]String generation...",
                total=n_total_variations,
            )

            for i, (param, n_words_per_topic, n_similar_words) in enumerate(
                all_parameters
            ):
                list_of_topics = [
                    [w.word for w in topic.words] for topic in param.topics
                ]
                string = generate_search_string(
                    list_of_topics=list_of_topics,
                    n_similar_words=n_similar_words,
                    n_words_per_topic=n_words_per_topic,
                    bert_model=bert_model,
                    bert_tokenizer=bert_tokenizer,
                    enrichment_text=enrichment_text,
                )

                search_strings.append(
                    {
                        "bertopic_parameters_id": param.id if is_bertopic else None,
                        "lda_parameters_id": param.id if is_lda else None,
                        "number_of_similar_words": n_similar_words,
                        "number_of_words_per_topic": n_words_per_topic,
                        "string": string,
                    }
                )

                progress.update(
                    task_id=string_generation_progess_task,
                    description=f"[green]String generation ({i + 1} of {n_total_variations})",  # noqa: E501
                    advance=1,
                    refresh=True,
                )

        with Session() as session:
            db.create_many_search_strings(
                search_strings=search_strings,
                session=session,
            )


@app.command()
def render_citation_graph(
    search_string_id: int = typer.Argument(
        ...,
        help="Id of the search string.",
    ),
    out_path: Path = typer.Argument(
        ...,
        exists=False,
        file_okay=False,
        dir_okay=False,
        help="Path to the output file, without any extensions",
    ),
):
    from sesg.graph import create_citation_graph, edges_to_adjacency_list

    with Session() as session:
        ss = db.get_search_string_by_id(
            search_string_id=search_string_id,
            session=session,
        )

        parameters = ss.lda_parameters or ss.bertopic_parameters

        if not parameters:
            raise RuntimeError(
                "Search string is not associated with a LDA or BERTopic parameter"
            )

        results_list = ss.metric.gs_studies_in_scopus

        slr = parameters.experiment.slr
        gs_studies = slr.gs_studies
        edges = db.get_slr_citation_edges(slr_id=slr.id, session=session)

    g = create_citation_graph(
        adjacency_list=edges_to_adjacency_list(edges=edges),
        tooltips={s.id: s.title for s in gs_studies},
        results_list=[r.id for r in results_list],
    )

    g.render(
        filename=out_path.stem + ".dot",
        directory=out_path.parent,
        format="pdf",
        view=True,
    )


if __name__ == "__main__":
    app()
