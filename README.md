# sesg

> SeSG (Search String Generator) python package repository.

[![PyPI version](https://badge.fury.io/py/sesg.svg)](https://badge.fury.io/py/sesg)
[![Documentation Status](https://readthedocs.org/projects/sesg/badge/?version=latest)](https://sesg.readthedocs.io/en/latest/?badge=latest)
[![CI](https://github.com/demetrius-mp/sesg/actions/workflows/pipeline.yaml/badge.svg)](https://github.com/demetrius-mp/sesg/actions/workflows/pipeline.yaml)
[![codecov](https://codecov.io/github/demetrius-mp/sesg/branch/main/graph/badge.svg?token=Y6DXNMDGU1)](https://codecov.io/github/demetrius-mp/sesg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v0.json)](https://github.com/charliermarsh/ruff)
[![Docstring Style](https://img.shields.io/badge/%20style-google-3666d6.svg)](https://google.github.io/styleguide/pyguide.html#s3.8-comments-and-docstrings)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

SeSG is a tool developed to help Systematic Literature Review researchers, specifically at the step of building a search string.

## Installation

You can install with `pip`, `poetry`, or any other package manager:

```bash
poetry add sesg
```

## Usage

> For a more extensive example, please refer to [this repository](https://github.com/demetrius-mp/sesg-cli).

### Generating a search string

```python
from dataclasses import dataclass
from random import sample

from sesg.search_string import (
    SimilarWordsFinder,
    create_enrichment_text,
    generate_search_string,
    set_pub_year_boundaries,
)
from sesg.topic_extraction import create_docs, extract_topics_with_bertopic
from transformers import BertForMaskedLM, BertTokenizer


@dataclass
class Study:
    title: str
    abstract: str
    keywords: str


GS: list[Study] = []
QGS: list[Study] = sample(GS, len(GS) // 3)


def main():
    docs = create_docs(
        [
            {
                "title": s.title,
                "abstract": s.abstract,
                "keywords": s.keywords,
            }
            for s in QGS
        ]
    )

    enrichment_text = create_enrichment_text(
        [
            {
                "title": s.title,
                "abstract": s.abstract,
            }
            for s in QGS
        ]
    )

    similar_words_finder = SimilarWordsFinder(
        enrichment_text=enrichment_text,
        bert_model=BertForMaskedLM.from_pretrained("bert-base-uncased"),
        bert_tokenizer=BertTokenizer.from_pretrained("bert-base-uncased"),
    )

    topics = extract_topics_with_bertopic(
        docs,
        kmeans_n_clusters=2,
        umap_n_neighbors=5,
    )

    search_string = generate_search_string(
        topics,
        n_words_per_topic=5,
        n_similar_words_per_word=1,
        similar_words_finder=similar_words_finder,
    )

    search_string = f"TITLE-ABS-KEY({search_string})"
    search_string = set_pub_year_boundaries(search_string, min_year=2010, max_year=2020)

    print(search_string)
    # TITLE-ABS-KEY((("antipatterns") AND ("detection" OR "management") AND ("bdtex") AND ("approach" OR "algorithm") AND ("smurf")) OR (("code" OR "pattern") AND ("detection" OR "management") AND ("design" OR "software") AND ("software" OR "computer") AND ("learning" OR "translation"))) AND PUBYEAR > 1999 AND PUBYEAR < 2018  # noqa: E501


if __name__ == "__main__":
    main()

```

### Assessing the quality of a search string

```python
import trio
from sesg.evaluation import EvaluationFactory, Study
from sesg.scopus import InvalidStringError, Page, ScopusClient


API_KEYS: list[str] = []

GS: list[Study] = []
QGS: list[Study] = []


async def main():
    string = 'TITLE-ABS-KEY("machine learning" and "code smell") AND PUBYEAR > 2010 AND PUBYEAR < 2020'  # noqa: E501
    evaluation_factory = EvaluationFactory(gs=GS, qgs=QGS)

    client = ScopusClient(API_KEYS)

    entries: list[Page.Entry] = []
    try:
        async for page in client.search(string):
            entries.extend(page.entries)

    except InvalidStringError:
        print("Invalid string")

    evaluation = evaluation_factory.evaluate([e.title for e in entries])

    print(evaluation.start_set_recall)
    # 0.7


if __name__ == "__main__":
    trio.run(main)
```

## Credits

This project is a continuation of [Leo Fuchs'](https://github.com/LeoFuchs/SeSG) work. Most of my work in this project consisted in refactoring the codebase, adding tests, improving the documentation and optimizing the performance, along with the addition of some new features.

## Highlights

Below you can find the major improvements over the original project:

- Added [**BERTopic**](https://github.com/MaartenGr/BERTopic) as a topic extraction strategy.
- Improved **snowballing** performance by 100x~120x (thanks to [rapidfuzz](https://github.com/maxbachmann/RapidFuzz) and [multiprocessing](https://docs.python.org/3.10/library/multiprocessing.html)).
- Improved **scopus search** performance by 30x~40x (thanks to [httpx](https://github.com/encode/httpx/) and [Eduardo Mendes'](https://github.com/dunossauro) help).
- Improved **search string generation** performance by ~1.5x (thanks to a caching system).
- Improved **code quality** by adopting the use of [lint](https://github.com/charliermarsh/ruff) and [formatting](https://github.com/psf/black) tools. Also, added [type hints](https://docs.python.org/3/library/typing.html) to try to catch errors before runtime.
- Added **tests** to prevent bugs when refactoring or adding new features.
- Added [**docs**](https://sesg.readthedocs.io/en/latest/) to help users and contributors.

## Contributing

You can contribute in many ways, such as [creating issues](https://github.com/demetrius-mp/sesg/issues) and [submitting pull requests](https://github.com/demetrius-mp/sesg/pulls). If you wish to contribute with code, please read the [contributor guide](https://sesg.readthedocs.io/en/latest/contributor-guide/).

## License

This project is licensed under the terms of the [GPL-3.0-only license](https://spdx.org/licenses/GPL-3.0-only.html).