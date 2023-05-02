"""Generate the code reference pages.

Refer to
https://mkdocstrings.github.io/recipes/#prevent-selection-of-prompts-and-output-in-python-code-blocks
"""

from pathlib import Path

import mkdocs_gen_files
from mkdocs_gen_files.nav import Nav as mkdocs_gen_files_Nav


nav = mkdocs_gen_files_Nav()


def is_private_module(parts: list[str]):
    return any((s.startswith("_") for s in parts))


for path in sorted(Path("src").rglob("*.py")):
    module_path = path.relative_to("src").with_suffix("")

    if not str(module_path).startswith("sesg"):
        continue

    doc_path = path.relative_to("src").with_suffix(".md")
    full_doc_path = Path("reference", doc_path)

    parts = list(module_path.parts)

    if parts[-1] == "__init__":
        parts = parts[:-1]
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")

    elif parts[-1] == "__main__":
        continue

    if is_private_module(parts):
        continue

    nav[parts] = doc_path.as_posix()  # type: ignore

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        identifier = ".".join(parts)
        print("::: " + identifier, file=fd)

    mkdocs_gen_files.set_edit_path(full_doc_path, path)


with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
