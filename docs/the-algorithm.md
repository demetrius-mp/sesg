---
hide:
  - navigation
---

# The algorithm

In this page you will find in-depth information of the proposed alogirhtm for SeSG.

SeSG is composed by 3 main steps:

- [Topic extraction](#topic-extraction)
- [Word enrichment](#word-enrichment)
- [Search string formulation](#search-string-formulation)

## Topic extraction

The topic extraction step consists of extracting the topics of a list of documents. In our context, each document is a relevant study provided by the user. Each document is composed by the title, abstract, and keywords of a study.

Each topic is supposed to be a set of words that represents the documents. Usually, a topic extraction algorithm will find a set of topics.

This package provides two topic extraction strategies: [LDA][sesg.topic_extraction.extract_topics_with_lda] and [BERTopic][sesg.topic_extraction.extract_topics_with_bertopic]. However, if you want to use another strategy, you can implement it having the following signature in mind:

```python
def extract_topics_with_custom_strategy(
  docs: list[str],
  **kwargs,  # your custom strategy parameters
) -> list[list[str]]:
  ...
```

Even though the topics contains a set of words that represents the documents, using only these words to directly formulate the search string may not provide enough completeness for the search string. To solve this problem, we must enrich each word of each topic.

## Word enrichment

This step consists of finding "similar words" of a given word, provided a context where the word is used. The context is composed by the title and abstract of the relevant studies provided by the user.

!!! note "What are similar words?"
    Similar words are words that are contextually similar, not with similar characters.

This package provides a BERT-based word enrichment strategy: [BERT][sesg.search_string.SimilarWordsFinder].

Below you will find details on the implementation of the strategy.

The similar words are extracted using BERT token prediction task. However, it is possible that BERT predicts tokens that are too similar character-wise. To filter out these character-wise similar words, we take two actions:

- Use Levenshtein edit distance to detect words that have a low edit distance.
- Use stemming to detect words with similar roots.

With this, we now have a list of similar words for each word of each topic. However, we still need to formulate the search string.

## Search string formulation

This step consists of combining the the topics, words, and similar words using boolean (AND, OR), operators. The combination is done with the following rules:

- Similar words of a word are combined with OR.
- Words of a topic are combined with AND.
- Topics are combined with OR.

Take the following example:

```python
topics = [["machine", "learning"], ["systematic", "review"]]

similar_words = [
  [["machine", "computer"], ["learning", "knowledge"]],
  [["systematic", "methodical"], ["review", "critique"]]
]

first_topic_representation = '(("machine" OR "computer") AND ("learning" OR "knowledge"))'
second_topic_representation = '(("systematic" OR "methodical") AND ("review" OR "critique"))'

search_string = f'{first_topic_representation} OR {second_topic_representation}'
```