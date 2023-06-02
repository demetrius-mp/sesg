# Contributor guide

In this section you will find information on how to contribute to this package.

## Development environment

### Recommended editor

This package is developed using primarily [vscode](https://code.visualstudio.com/). We provide some configuration files such as recommended extensions, and settings. You can find them in the `.vscode` folder.

### Package and dependency manager

The package manager (dependencies/packaging) used for development is [poetry](https://python-poetry.org/). To install poetry, please refer to the [installation docs](https://python-poetry.org/docs/#installation).

To install all of the project dependencies (including tests, docs, and development dependencies), run the following command:

```sh
poetry install
```

If you only want to install some groups of dependencies, please refer to [poetry docs](https://python-poetry.org/docs/cli#install).

After installing the project, you can open a `shell` within the virtual environment with the following command:

```sh
poetry shell
```

## Development workflow

We use [poethepoet](https://github.com/nat-n/poethepoet) as the task runner. You can see the available tasks by running the following command:

```sh
poe --help
```

The most important tasks are `test` and `format`. The first one runs the test suite, and the second one will lint and format the code, and also format the `pyproject.toml` file.

To run the test suite, use the following command:

```sh
poe test
```

To lint and format the code, use the following command:

```sh
poe format
```

??? note
    Please notice that the `poe` command only exists within the virtual environment. This means you need to either enter the virtual environment shell, or run the following command:

    ```sh
    poetry run poe test  # poetry run poe task_name
    ```

    Check out [poetry run](https://python-poetry.org/docs/cli#run) docs.

!!! info
    Don't forget to run the test suite before pushing to avoid failing the CI tests. To help avoiding CI fails, we use [pre-commit](https://pre-commit.com/) hooks on the [pre-push](https://pre-commit.com/#confining-hooks-to-run-at-certain-stages) stage. This means that some tasks that are executed in CI (such as formatting) are also executed as a pre-push hook.
