from dataclasses import dataclass
from pathlib import Path
from typing import List

import tomli
from dacite import from_dict


@dataclass
class LDAParameters:
    min_document_frequency: List[float]
    number_of_topics: List[int]


@dataclass
class StringFormulationParameters:
    number_of_words_per_topic: List[int]
    number_of_similar_words: List[int]


@dataclass
class Config:
    scopus_api_keys: List[str]
    string_formulation_parameters: StringFormulationParameters
    lda_parameters: LDAParameters


def get_config(config_file_path: Path) -> Config:
    with open(config_file_path, "rb") as f:
        settings_dict = tomli.load(f)

    return from_dict(Config, settings_dict)
