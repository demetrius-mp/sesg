# Contributor guide

In this section you will find information on how to contribute to this package.

## Development environment

This package is developed using primarily [vscode](https://code.visualstudio.com/). We highly recommend it, which is why we provide some environment configuration files such as recommended extensions.

The code is linted with [ruff](https://github.com/charliermarsh/ruff), and formatted with [black](https://github.com/psf/black).


## Typos and bad-written documentation

Found a typo or bad-written documentation? Instead of opening a PR, please open an [issue](https://github.com/demetrius-mp/sesg/issues).

## Code contributions

Below you will find some notes on how to write code that is consistent with the already existing code.

- Functions **must** have return type annotations
- Function arguments with "easy" types (e.g., primitives, lists, iterators) **must** be annotated
- Functions **must** have google-style docstrings with `description`, `args`, and `returns` sections.
- Function docstrings **should** have an `examples` section.
- **Must** use list or generator comprehensions instead of `#!python map` and `#!python filter`.
- **Avoid** premature optimization.
- When annotating with types, **prefer** begin as concise as possible. For example, if you function returns a `#!python list[str]`, annotate with `#!python list[str]` instead of `#!python Iterable[str]` or `#!python Iterator[str]`. However, if your function `#!python yield`s a string, annotate with `#!python Iterator[str]` instead of `#!python Generator[None, None, str]`.
