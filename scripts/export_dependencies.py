import shutil
import subprocess
from pathlib import Path

import tomli


def main():
    requirements_folder = Path.cwd() / "requirements"

    if requirements_folder.exists():
        shutil.rmtree(requirements_folder)

    requirements_folder.mkdir()

    with open(requirements_folder / ".gitkeep", "w") as f:
        ...

    pyproject_toml_path = Path.cwd() / "pyproject.toml"

    with open(pyproject_toml_path, "rb") as f:
        pyproject = tomli.load(f)

    groups = pyproject["tool"]["poetry"]["group"]
    groups_names = [name for name in groups]

    # exporting package requirements
    subprocess.run(
        "poetry export -o requirements/requirements.txt --without-hashes --without-urls",  # noqa: E501
        shell=True,
    )

    # exporting groups requirements
    for group in groups_names:
        subprocess.run(
            f"poetry export --only={group} -o requirements/requirements-{group}.txt --without-hashes --without-urls",  # noqa: E501
            shell=True,
        )


if __name__ == "__main__":
    main()
