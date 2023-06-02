from dataclasses import dataclass

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


studies: list[Study] = []


def main():
    docs = create_docs(
        [
            {
                "title": s.title,
                "abstract": s.abstract,
                "keywords": s.keywords,
            }
            for s in studies
        ]
    )

    enrichment_text = create_enrichment_text(
        [
            {
                "title": s.title,
                "abstract": s.abstract,
            }
            for s in studies
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
