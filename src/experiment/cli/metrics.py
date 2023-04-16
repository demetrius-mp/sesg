from typing import List

import typer
from rich import print
from rich.progress import Progress
from sesg.topic_extraction import TopicExtractionStrategy

from experiment.database import queries as db
from experiment.database.core import Session


app = typer.Typer(rich_markup_mode="markdown")


@app.command()
def extract(
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
        "--for",
        case_sensitive=False,
        help="The Topic extraction method that was used to generate the search strings that will be used against Scopus.",  # noqa: E501
    ),
):
    from sesg import graph, metrics

    from experiment.database.compression import decompress_scopus_titles

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

        gs_studies = slr.gs_studies
        qgs_studies = experiment.qgs_studies

        citation_edges = db.get_slr_citation_edges(
            slr_id=slr.id,
            session=session,
        )

        search_strings = db.get_many_search_strings(
            experiment_id=experiment.id,
            session=session,
            topic_extraction_strategy=topic_extraction_strategy,
        )

    processed_gs_titles = [
        metrics.preprocess_string(string=s.title) for s in gs_studies
    ]
    processed_qgs_titles = [
        metrics.preprocess_string(string=s.title) for s in qgs_studies
    ]

    adjacency_list = graph.edges_to_adjacency_list(
        edges=citation_edges,
    )
    undirected_adjacency_list = graph.edges_to_adjacency_list(
        edges=citation_edges,
        directed=False,
    )

    list_of_metrics: List[db.MetricData] = list()

    with Session() as session, Progress() as progress:
        strings_progress_task = progress.add_task(
            "[green]Calculating metrics...",
            total=len(search_strings),
        )

        for ss in search_strings:
            scopus_results = decompress_scopus_titles(
                ss.scopus_result.compressed_titles
            )
            processed_scopus_titles = [
                metrics.preprocess_string(string=r) for r in scopus_results
            ]

            qgs_studies_in_scopus = metrics.similarity_score(
                small_set=processed_qgs_titles,
                other_set=processed_scopus_titles,
            )
            qgs_studies_in_scopus = [qgs_studies[i] for i, _ in qgs_studies_in_scopus]

            gs_studies_in_scopus = metrics.similarity_score(
                small_set=processed_gs_titles,
                other_set=processed_scopus_titles,
            )
            gs_studies_in_scopus = [gs_studies[i] for i, _ in gs_studies_in_scopus]

            gs_studies_in_scopus_and_bsb = graph.serial_breadth_first_search(
                adjacency_list=adjacency_list,
                starting_nodes=[s.id for s in gs_studies_in_scopus],
            )

            gs_studies_in_scopus_and_bsb_and_fsb = graph.serial_breadth_first_search(
                adjacency_list=undirected_adjacency_list,
                starting_nodes=[s.id for s in gs_studies_in_scopus],
            )

            metric = metrics.Metrics(
                gs_size=len(gs_studies),
                n_scopus_results=len(scopus_results),
                n_qgs_studies_in_scopus=len(qgs_studies_in_scopus),
                n_gs_studies_in_scopus=len(gs_studies_in_scopus),
                n_gs_studies_in_scopus_and_bsb=len(gs_studies_in_scopus_and_bsb),
                n_gs_studies_in_scopus_and_bsb_and_fsb=len(
                    gs_studies_in_scopus_and_bsb_and_fsb
                ),
            )

            metric_data: db.MetricData = {
                "search_string_id": ss.id,
                "gs_studies_in_scopus": [s.id for s in gs_studies_in_scopus],
                "gs_studies_in_scopus_and_bsb": gs_studies_in_scopus_and_bsb,
                "gs_studies_in_scopus_and_bsb_and_fsb": gs_studies_in_scopus_and_bsb_and_fsb,  # noqa: E501
                "qgs_studies_in_scopus": [s.id for s in qgs_studies_in_scopus],
                "scopus_precision": metric.scopus_precision,
                "scopus_recall": metric.scopus_recall,
                "scopus_f1_score": metric.scopus_f1_score,
                "scopus_and_bsb_recall": metric.scopus_and_bsb_recall,
                "scopus_and_bsb_and_fsb_recall": metric.scopus_and_bsb_and_fsb_recall,  # noqa: E501
                "n_scopus_results": metric.n_scopus_results,
            }

            list_of_metrics.append(metric_data)

            progress.update(
                strings_progress_task,
                advance=1,
                refresh=True,
            )

        db.create_many_metrics(
            gs_studies=gs_studies,
            metrics=list_of_metrics,
            session=session,
        )


if __name__ == "__main__":
    app()
