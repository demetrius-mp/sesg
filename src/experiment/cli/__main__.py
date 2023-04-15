from importlib import import_module
from pathlib import Path

import typer


def include_cli_apps(app: typer.Typer):
    for path in Path(__file__).parent.iterdir():
        # ignore dunder entries, such as
        # __init__.py, __main__.py, __pycache__/, etc.
        if path.stem.startswith("__") and path.stem.endswith("__"):
            continue

        cli_module_name = path.stem
        module = import_module(f"experiment.cli.{cli_module_name}")
        app.add_typer(module.app, name=cli_module_name.replace("_", "-"))


if __name__ == "__main__":
    app = typer.Typer(rich_markup_mode="markdown")

    include_cli_apps(app)

    app()
