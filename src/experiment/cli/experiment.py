import typer
from rich import print

from experiment.database import queries as db
from experiment.database.core import Session


app = typer.Typer(rich_markup_mode="markdown")


@app.command()
def create(
    slr_name: str = typer.Argument(
        ...,
        help="Name of the Systematic Literature Review",
    ),
    experiment_name: str = typer.Argument(
        ...,
        help="Name of the Experiment",
    ),
    qgs_size: int = typer.Argument(
        ...,
        help="Size of the QGS for this experiment",
    ),
):
    from random import sample

    with Session() as session:
        slr = db.get_slr_by_name(
            name=slr_name,
            session=session,
        )
        gs_studies = slr.gs_studies

    if qgs_size > len(gs_studies):
        raise RuntimeError(
            f"QGS size can't be higher than the number of studies in the GS ({qgs_size} > {len(gs_studies)})"  # noqa: E501
        )

    random_qgs = sample(gs_studies, k=qgs_size)

    with Session() as session:
        experiment = db.create_experiment(
            slr_id=slr.id,
            slr_gs_studies=slr.gs_studies,
            experiment_name=experiment_name,
            qgs_studies=random_qgs,
            session=session,
        )

    print(f"Created {experiment} with the following QGS:")
    for study in experiment.qgs_studies:
        print(f'Study(id={study.id}, title="{study.title}", slr_id={study.slr_id})')


if __name__ == "__main__":
    app()
