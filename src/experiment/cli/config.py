from dataclasses import asdict
from pathlib import Path

import tomli_w
import typer

from experiment import config


app = typer.Typer(rich_markup_mode="markdown")


@app.command()
def init(
    out_folder: Path = typer.Argument(
        Path.cwd(),
        help="Path to a folder where the configuration files will be created.",  # noqa: E501
        dir_okay=True,
        file_okay=False,
        exists=True,
    )
):
    base_lda_parameters = config.LDAParameters(
        min_document_frequency=[0.1, 0.2, 0.3, 0.4],
        number_of_topics=[1, 2, 3, 4, 5],
    )

    base_string_formulation_parameters = config.StringFormulationParameters(
        number_of_words_per_topic=[5, 6, 7, 8, 9, 10],
        number_of_similar_words=[0, 1, 2, 3],
    )

    base_settings = config.Config(
        scopus_api_keys=["key1", "key2", "key3"],
        lda_parameters=base_lda_parameters,
        string_formulation_parameters=base_string_formulation_parameters,
    )

    base_settings = asdict(base_settings)

    with open(out_folder / "settings.toml", "wb") as f:
        tomli_w.dump(base_settings, f)


if __name__ == "__main__":
    app()
