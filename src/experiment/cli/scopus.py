import asyncio
from functools import wraps
from pathlib import Path
from typing import List

import typer
from experiment.database import queries as db
from experiment.database.core import Session
from experiment.settings import get_settings
from rich import print
from rich.progress import Progress
from sesg.topic_extraction import TopicExtractionStrategy


class AsyncTyper(typer.Typer):
    def async_command(self, *args, **kwargs):
        def decorator(async_func):
            @wraps(async_func)
            def sync_func(*_args, **_kwargs):
                return asyncio.run(async_func(*_args, **_kwargs))

            self.command(*args, **kwargs)(sync_func)
            return async_func

        return decorator


app = AsyncTyper(rich_markup_mode="markdown")


@app.async_command()
async def get_results(
    slr_name: str = typer.Argument(
        ...,
        help="Name of the Systematic Literature Review",
    ),
    experiment_name: str = typer.Argument(
        ...,
        help="Name of the Experiment",
    ),
    topic_extraction_strategy: TopicExtractionStrategy = typer.Option(
        ...,
        "--topic-extraction-strategy",
        "-s",
        case_sensitive=False,
        help="The Topic extraction method that used to generate the search strings that will be used against Scopus.",  # noqa: E501
    ),
    settings_file_path: Path = typer.Option(
        Path.cwd() / "settings.toml",
        "--setings-file-path",
        "-f",
        help="Path to the `settings.toml` file",
    ),
    timeout: int = typer.Option(
        5,
        "--timeout",
        "-t",
        help="Time in seconds to wait for an API response before retrying.",
    ),
    timeout_attempts: int = typer.Option(
        10,
        "--timeout-attempts",
        "-a",
        help="How much times in a row to redo a timed out request.",
    ),
):
    from experiment.database.compression import compress_scopus_titles
    from sesg.scopus_client import ScopusClient
    from sesg.search_string import set_pub_year

    settings = get_settings(
        settings_file_path=settings_file_path,
    )

    print("Querying database...")

    with Session() as session:
        slr = db.get_slr_by_name(
            name=slr_name,
            session=session,
        )
        experiment = db.get_experiment_by_name(
            slr_id=slr.id,
            experiment_name=experiment_name,
            session=session,
        )

        search_strings = db.get_many_search_strings(
            experiment_id=experiment.id,
            session=session,
            topic_extraction_strategy=topic_extraction_strategy,
        )

        if len(search_strings) == 0:
            print("[red]No search strings were found.")
            raise typer.Abort()

        first_id = db.get_last_used_search_string_id(
            experiment_id=experiment.id,
            topic_extraction_strategy=topic_extraction_strategy,
            session=session,
        )

        print(f"Found {len(search_strings)} strings.")

        if first_id is not None:
            last_used_string_index = first_id - search_strings[0].id
            print(
                f"The `id` of the last used string is {first_id} "
                f"({last_used_string_index + 1} of {len(search_strings)})"
            )
            search_strings = search_strings[last_used_string_index + 1 :]

        if first_id is None:
            print("No strings were used before.")

        if len(search_strings) == 0:
            print("[red]All strings were already used.")
            raise typer.Abort()

    client = ScopusClient(
        timeout=timeout,
        api_keys=settings.scopus_api_keys,
        timeout_attempts=timeout_attempts,
    )

    with Session() as session, Progress() as progress:
        strings_progress_task = progress.add_task(
            "[green]Searching strings...",
            total=len(search_strings),
        )
        for search_string_index, ss in enumerate(search_strings):
            description = f"String {search_string_index + 1} of {len(search_strings)}"

            progress.update(
                strings_progress_task,
                description=description,
                refresh=True,
            )

            string = ss.string
            string = f"TITLE-ABS-KEY({string})"
            string = set_pub_year(
                string=string,
                max_year=slr.max_publication_year,
                min_year=slr.min_publication_year,
            )

            paging_task = progress.add_task(description="[blue]Paging results...")

            scopus_titles: List[str] = list()

            async for data in client.search(query=string):
                if isinstance(data, ScopusClient.SearchResults):
                    if data.current_page == 0:
                        progress.update(
                            paging_task,
                            total=data.number_of_pages,
                            refresh=True,
                        )

                    description = (
                        f"Page {data.current_page + 1} of {data.number_of_pages}"
                    )

                    progress.update(
                        paging_task,
                        description=description,
                        advance=1,
                        refresh=True,
                    )

                    scopus_titles.extend((r.title for r in data.entries))

                if isinstance(data, ScopusClient.APIKeyExpiredError):
                    print(
                        f"API Key {data.api_key_index + 1} of {len(settings.scopus_api_keys)} is expired."  # noqa: E501
                    )
                    if data.resets_at:
                        resets_at = data.resets_at.strftime("%d/%m/%Y %H:%M:%S")
                        print(f"Resets at {resets_at}")
                        print()

                if isinstance(data, ScopusClient.APITimeoutError):
                    print(
                        f"Timed out on page {data.current_page}. {timeout_attempts - data.current_attempt - 1} attempts left"  # noqa: E501
                    )
                    print()

            db.create_scopus_result(
                search_string_id=ss.id,
                session=session,
                compressed_titles=compress_scopus_titles(scopus_titles),
            )

            progress.remove_task(paging_task)
            progress.update(
                strings_progress_task,
                advance=1,
                refresh=True,
            )


if __name__ == "__main__":
    app()
