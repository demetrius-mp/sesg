import shutil
import subprocess
from multiprocessing import Pool
from pathlib import Path
from typing import List, Optional

import tomli


def export_dependencies_from_group(
    group: Optional[str] = None,
) -> None:
    if group is None:
        # exporting package requirements
        subprocess.run(
            "poetry export -o requirements/package.piprequirements --without-hashes --without-urls",  # noqa: E501
            shell=True,
        )

    else:
        subprocess.run(
            f"poetry export --only={group} -o requirements/{group}.piprequirements --without-hashes --without-urls",  # noqa: E501
            shell=True,
        )


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
    groups_names: List[str] = [name for name in groups]

    with Pool() as pool:
        pool.map(
            export_dependencies_from_group,
            [None, *groups_names],
        )

    print("Exported all dependencies by group.")


if __name__ == "__main__":
    main()
