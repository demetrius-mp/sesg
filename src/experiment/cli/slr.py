import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import typer
from dacite import from_dict
from rich import print
from rich.progress import Progress
from rich.prompt import Confirm

from experiment.database import queries as db
from experiment.database.core import Session


app = typer.Typer(rich_markup_mode="markdown")


@dataclass
class SLRJSONData:
    @dataclass
    class SLRJSONStudyData:
        id: int
        title: str
        abstract: str
        keywords: str

    name: str
    gs: List[SLRJSONStudyData]
    min_publication_year: Optional[int]
    max_publication_year: Optional[int]


@app.command()
def create_from_json(
    json_file_path: Path = typer.Argument(
        ...,
        help="Path to a `slr.json` file",
        dir_okay=False,
        file_okay=True,
        exists=True,
    ),
):
    with open(json_file_path, "r") as f:
        data = json.load(f)
        slr_json = from_dict(SLRJSONData, data)

    print("Confirm that the data is correct:")
    slr_confirm_data = {
        "name": slr_json.name,
        "min_publication_year": slr_json.min_publication_year,
        "ma_publication_year": slr_json.max_publication_year,
    }

    print(slr_confirm_data)

    confirmed = Confirm.ask(
        "Is the SLR data correct?",
        default=True,
    )

    if not confirmed:
        raise typer.Abort()

    for study in slr_json.gs:
        study_confirm_data = {
            "title": study.title,
            "keywords": study.keywords,
        }

        print(study_confirm_data)

    confirmed = Confirm.ask(
        "Is the SLR GS correct?",
        default=True,
    )

    if not confirmed:
        raise typer.Abort()

    with Session() as session:
        slr = db.create_slr_with_gs(
            name=slr_json.name,
            min_publication_year=slr_json.min_publication_year,
            max_publication_year=slr_json.max_publication_year,
            session=session,
            gs_studies=[
                {
                    "abstract": study.abstract,
                    "keywords": study.keywords,
                    "title": study.title,
                }
                for study in slr_json.gs
            ],
        )

        print(f"Created {slr}")

    print(f"Created `{slr_json}`")


@app.command()
def create(
    name: str = typer.Argument(
        ...,
        help="Name of the Systematic Literature Review",
    ),
    min_publication_year: Optional[int] = typer.Option(
        None,
        "--min-year",
        help="Minimum publication year.",
    ),
    max_publication_year: Optional[int] = typer.Option(
        None,
        "--max-year",
        help="Maximum publication year.",
    ),
):
    with Session() as session:
        slr = db.create_slr(
            name=name,
            min_publication_year=min_publication_year,
            max_publication_year=max_publication_year,
            session=session,
        )

    print(f"Created `{slr}`")


def _read_studies_from_json(
    studies_json_path: Path,
):
    @dataclass
    class Study:
        id: int
        title: str
        abstract: str
        keywords: str

    with open(studies_json_path, "r") as f:
        json_data = json.load(f)

    studies: List[Study] = list()

    for study_json in json_data:
        study = from_dict(Study, study_json)

        studies.append(study)

    return studies


@app.command()
def save_gs_from_json(
    slr_name: str = typer.Argument(
        ...,
        help="Name of the Systematic Literature Review",
    ),
    gs_json_path: Path = typer.Argument(
        ...,
        help="Path to a gs.json file",
        dir_okay=False,
        file_okay=True,
        exists=True,
    ),
):
    with Session() as session:
        slr = db.get_slr_by_name(
            name=slr_name,
            session=session,
        )
        gs_studies = _read_studies_from_json(gs_json_path)

        studies = db.add_many_studies_to_slr(
            session=session,
            slr_id=slr.id,
            studies=[
                {
                    "abstract": s.abstract,
                    "keywords": s.keywords,
                    "title": s.title,
                }
                for s in gs_studies
            ],
        )

        print(f"Created {len(studies)} studies:")
        for study in studies:
            print(f'Study(id={study.id}, title="{study.title}", slr_id={study.slr_id})')


@app.command()
def snowballing(
    slr_name: str = typer.Argument(
        ...,
        help="Name of the Systematic Literature Review",
    ),
    txts_path: Path = typer.Argument(
        ...,
        help="Path to a folder with the studies `.cermtxt` files",
        dir_okay=True,
        file_okay=False,
        exists=True,
    ),
):
    from sesg.snowballing import (
        SnowballingStudy,
        backward_snowballing,
    )

    with Session() as session:
        slr = db.get_slr_by_name(
            name=slr_name,
            session=session,
        )
        gs_studies = slr.gs_studies
        edges = db.get_slr_citation_edges(
            slr_id=slr.id,
            session=session,
        )

    if len(edges) > 0:
        print("[red]Snowballing was already executed for this SLR.")
        raise typer.Abort()

    sb_studies: List[SnowballingStudy] = []

    for i, study in enumerate(gs_studies):
        with open(txts_path / f"{i + 1}.cermtxt", "r") as f:
            text_content = f.read()

        sb_study = SnowballingStudy(
            id=study.id,
            title=study.title,
            text_content=text_content,
        )

        sb_studies.append(sb_study)

    with Session() as session, Progress() as progress:
        snowballing_progress_task = progress.add_task(
            "[green]Snowballing...",
            total=len(sb_studies),
        )

        bsb_iterator = backward_snowballing(studies=sb_studies)

        for i, (study, references) in enumerate(bsb_iterator):
            if len(references) > 0:
                db.add_study_references(
                    slr_gs_studies=slr.gs_studies,
                    study_id=study.id,
                    references=[r.id for r in references],
                    session=session,
                )

            print(f"{study.id} -> {[r.id for r in references]}")

            progress.update(
                snowballing_progress_task,
                description=f"[green]Snowballing ({i + 1} of {len(sb_studies)})",
                advance=1,
                refresh=True,
            )


@app.command()
def render_citation_graph(
    slr_name: str = typer.Argument(
        ...,
        help="Name of the Systematic Literature Review",
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
        slr = db.get_slr_by_name(
            name=slr_name,
            session=session,
        )
        gs_studies = slr.gs_studies
        edges = db.get_slr_citation_edges(
            slr_id=slr.id,
            session=session,
        )

    g = create_citation_graph(
        adjacency_list=edges_to_adjacency_list(edges=edges),
        tooltips={s.id: s.title for s in gs_studies},
    )

    g.render(
        filename=out_path.stem + ".dot",
        directory=out_path.parent,
        format="pdf",
        view=True,
    )


if __name__ == "__main__":
    app()
