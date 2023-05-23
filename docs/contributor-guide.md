# Contributor guide

In this section you will find information on how to contribute to this package.

## Development environment

This package is developed using primarily [vscode](https://code.visualstudio.com/). We highly recommend it, which is why we provide some environment configuration files such as recommended extensions.

The code is linted with [ruff](https://github.com/charliermarsh/ruff), and formatted with [black](https://github.com/psf/black).

The package manager (dependencies/packaging) used for development is [poetry](https://python-poetry.org/). To install all of the dependencies (including tests, docs, and development dependencies), run the following command:

```sh
poetry install
```

If you only want to install some groups of dependencies, please refer to [poetry docs](https://python-poetry.org/docs/cli#install).

After installing the project, you can open a `shell` within the virtual environment with the following command:

```sh
poetry shell
```

## Development workflow

We use [poethepoet](https://github.com/nat-n/poethepoet) as the task runner. You can find the available tasks on the [`pyproject.toml`](https://github.com/demetrius-mp/sesg/blob/main/pyproject.toml) file, under the `tool.poe.tasks.*` key.

The most common development tasks are `test`, and `format`. To run a task, you can use the following command:

```sh
poe test  # poe task_name
```

??? note
    Please notice that the `poe` command only exists within the virtual environment. This means you need to either enter the virtual environment shell, or run the following command:

    ```sh
    poetry run poe test  # poetry run poe task_name
    ```

    Check out [poetry run](https://python-poetry.org/docs/cli#run) docs.

Don't forget to run the test suite before pushing to avoid failing the CI tests. To help avoiding CI fails, we use [pre-commit](https://pre-commit.com/) hooks on the [pre-push](https://pre-commit.com/#confining-hooks-to-run-at-certain-stages) stage. This means that some tasks that are executed in CI (such as formatting and testing) are also executed as a pre-push hook.