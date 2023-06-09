from typing import Any

import pytest
from sesg.search_string.generation import (
    generate_search_string,
    generate_search_string_with_similar_words,
    generate_search_string_without_similar_words,
)
from sesg.similar_words import BertSimilarWordsGenerator
from transformers import BertForMaskedLM, BertTokenizer  # type: ignore


@pytest.fixture(scope="package")
def bert_models():
    bert_tokenizer: Any = BertTokenizer.from_pretrained("bert-base-uncased")
    bert_model: Any = BertForMaskedLM.from_pretrained("bert-base-uncased")

    bert_model.eval()

    return bert_tokenizer, bert_model


@pytest.fixture(scope="package")
def enrichment_text():
    enrichment_text = """A business goal-based approach to achieving systems engineering capability maturity Any process improvement program should be driven by and related to some set of business or overarching organizational needs. By considering change drivers in concert with the organization strategic objectives and "pains" one can develop a vision of the desired state, what the organization should look like and how it should behave after the desired changes are achieved. An appropriate reference model is then chosen and used in an assessment to identify improvement opportunities. Based on the assessment findings an action plan is developed and implemented which addresses both specific process changes and organization cultural issues. Finally, an appropriate set of measures is defined and implemented to help measure the effects of the various changes.
Bridging the Gap between Business Strategy and Software Development In software-intensive organizations, an organizational management system will not guarantee organizational success unless the business strategy can be translated into a set of operational software goals. The Goal Question Metric (GQM) approach has proven itself useful in a variety of industrial settings to support quantitative software project management. However, it does not address linking software measurement goals to higher-level goals of the organization in which the software is being developed. This linkage is important, as it helps to justify software measurement efforts and allows measurement data to contribute to higher-level decisions. In this paper, we propose a GQM+Strategies?measurement approach that builds on the GQM approach to plan and implement software measurement. GQM+Strategies® provides mechanisms for explicitly linking software measurement goals to higher-level goals for the software organization, and further to goals and strategies at the level of the entire business. An example application of the proposed method is illustrated in the context of an example measurement initiative.
GQM + Strategies: A comprehensive methodology for aligning business strategies with software measurement In software-intensive organizations, an organizational management system will not guarantee organizational success unless the business strategy can be translated into a set of operational software goals. The Goal Question Metric (GQM) approach has proven itself useful in a variety of industrial settings to support quantitative software project management. However, it does not address linking software measurement goals to higher-level goals of the organization in which the software is being developed. This linkage is important, as it helps to justify software measurement efforts and allows measurement data to contribute to higher-level decisions. In this paper, we propose a GQM+Strategies(R) measurement approach that builds on the GQM approach to plan and implement software measurement. GQM+Strategies(R) provides mechanisms for explicitly linking software measurement goals to higher-level goals for the software organization, and further to goals and strategies at the level of the entire business. The proposed method is illustrated in the context of an example application of the method.
Software Engineering Strategies: Aligning Software Process Improvement with Strategic Goals Aligning software process improvement with the business and strategic goals of an enterprise is a key success factor for process improvement. Software process improvement methods typically only provide little or generic guidance for goal centered process improvements. We provide a framework for developing software engineering strategies that are aligned with corporate strategies and goals. Strategic objects as an important part of our framework can be directly aligned with SPICE or CMMI processes. This allows that any process improvement action can be systematically aligned with strategic goals.
Application of GQM+Strategies(R) in the Japanese space industry Aligning organizational goals and activities is of great importance for large organizations in order to improve their performance and achieve top-level business goals. Through alignment, organizational sub-units can optimize and explicitly highlight their contributions towards the achievement of top-level business goals. GQM + Strategies 1 provides a systematic, measurement-based approach for explicitly linking goals and contributions on different organizational levels. This paper presents results and experiences from applying the GQM + Strategies approach at the Japan Aerospace Exploration Agency.
Aligning Organizations Through Measurement: The GQM+Strategies Approach Aligning an organization’s goals and strategies requires specifying their rationales and connections so that the links are explicit and allow for analytic reasoning about what is successful and where improvement is necessary. This book provides guidance on how to achieve this alignment, how to monitor the success of goals and strategies and use measurement to recognize potential failures, and how to close alignment gaps. It uses the GQM+Strategies approach, which provides concepts and actionable steps for creating the link between goals and strategies across an organization and allows for measurement-based decision-making. After outlining the general motivation for organizational alignment through measurement, the GQM+Strategies approach is described concisely, with a focus on the basic model that is created and the process for creating and using this model. The recommended steps of all six phases of the process are then described in detail with the help of a comprehensive application example. Finally, the industrial challenges addressed by the method and cases of its application in industry are presented, and the relations to other approaches, such as Balanced Scorecard, are described. The book concludes with supplementary material, such as checklists and guidelines, to support the application of the method. This book is aimed at organization leaders, managers, decision makers, and other professionals interested in aligning their organization’s goals and strategies and establishing an efficient strategic measurement program. It is also interesting for academic researchers looking for mechanisms to integrate their research results into organizational environments.
Aligning Software-related Strategies in Multi-Organizational Settings Aligning the activities of an organization with its business goals is a challenging task that is critical for success. Alignment in a multi-organizational setting requires the integration of different internal or external organizational units. The anticipated benefits of multi-organizational alignment consist of clarified contributions and increased transparency of the involved organizational units. The GQM+Strategies approach provides mechanisms for explicitly linking goals and strategies within an organization and is based on goal-oriented measurement. This paper presents the process and first-hand experience of applying GQM+Strategies in a multi-organizational setting from the aerospace industry. Additionally, the resulting GQM+Strategies grid is sketched and selected parts are discussed. Finally, the results are reflected on and an overview of future work is given.
Integration of strategic management, process improvement and quantitative measurement for managing the competitiveness of software engineering organizations Strategic management is a key discipline that permits companies to achieve their competitive goals. An effective and explicit alignment and integration of business strategy with SPI initiatives based on measurement is essential to prevent loss of income, customers and competitiveness. By integrating SPI models and measurement techniques in the strategy management process, an organization’s investments will be better aligned with strategy, optimizing the benefits obtained as a result of an SPI program. In this paper, the authors propose BOQM (Balanced Objective-Quantifiers Methodology) that integrates properly strategic management, process improvement and quantitative measurement to manage the competitiveness of software engineering organizations. Finally, this paper presents and discusses the results from implementing BOQM in a software development organization.
Strategically Balanced Process Adoption Software processes have an important role to play in realizing organizational strategies. When a software organization is about to decide on the adoption of a new process, it should have a clear understanding of its own strategic objectives, as well as the potentials of the new method in supporting or hindering its strategic plan. From this perspective, a successful process adoption initiative is one which provides maximum support to the strategic objectives of an organization while producing a minimum of adverse effects. This paper introduces the concept of Strategically Balanced Process Adoption (SBPA) for anticipating and monitoring the strategic impacts of a new process before and after its adoption. A set of techniques are proposed for the realization of SBPA, which are based on a repository of method fragments, introduced in an earlier ICSP paper. The proposed techniques are deployed in an industrial experience, where the subject organization was about to adopt a custom-designed agile process. The proposed techniques of SBPA helped the subject organization to better design the to-be process, with improved control over its enactment.
Applying and adjusting a software process improvement model in practice: the use of the IDEAL model in a small software enterprise Software process improvement is a demanding and complex undertaking. To support the constitution and implementation of software process improvement schemes the Software Engineering Institute (SEI) proposes a framework, the so-called IDEAL model. This model is based on experiences from large organizations. The aim of the research described here was to investigate the suitability of the model for small software enterprises. It has therefore been deployed and adjusted for successful use in a small Danish software company. The course of the project and the application of the model are presented and the case is reflected on the background of current knowledge about managing software process improvement as organizational change.""".strip()

    return enrichment_text


@pytest.fixture(scope="module")
def bert_similar_words_generator(
    bert_models,
    enrichment_text,
):
    bert_tokenizer, bert_model = bert_models

    generate_similar_words = BertSimilarWordsGenerator(
        bert_model=bert_model,
        bert_tokenizer=bert_tokenizer,
        enrichment_text=enrichment_text,
    )

    return generate_similar_words


@pytest.mark.parametrize(
    "topics,n_words_per_topic,expected",
    [
        (
            [["t11", "t12", "t13"], ["t21", "t22", "t23"]],
            2,
            '("t11" AND "t12") OR ("t21" AND "t22")',
        ),
        (
            [["t11", "t12", "t13"], ["t21", "t22", "t23"]],
            3,
            '("t11" AND "t12" AND "t13") OR ("t21" AND "t22" AND "t23")',
        ),
    ],
)
def test_generate_search_string_without_similar_words(
    topics,
    n_words_per_topic,
    expected,
):
    result = generate_search_string_without_similar_words(
        topics=topics,
        n_words_per_topic=n_words_per_topic,
    )

    assert result == expected


def test_generate_search_string_with_similar_words(
    bert_similar_words_generator: BertSimilarWordsGenerator,
):
    result = generate_search_string_with_similar_words(
        topics=[
            ["software", "measurement", "gqm"],
            ["process", "software", "strategic"],
        ],
        n_similar_words_per_word=2,
        n_words_per_topic=2,
        similar_words_generator=bert_similar_words_generator,
    )
    expected = '(("software" OR "management" OR "development") AND ("measurement" OR "development" OR "design")) OR (("process" OR "software" OR "business") AND ("software" OR "management" OR "development"))'

    assert result == expected


def test_generate_search_string_with_0_similar_words_should_return_result_of_generate_search_string_without_similar_words(
    bert_similar_words_generator: BertSimilarWordsGenerator,
):
    n_words_per_topic = 2

    result = generate_search_string(
        topics=[
            ["software", "measurement", "gqm"],
            ["process", "software", "strategic"],
        ],
        n_words_per_topic=n_words_per_topic,
        n_similar_words_per_word=0,
        similar_words_generator=bert_similar_words_generator,
    )

    expected = generate_search_string_without_similar_words(
        topics=[
            ["software", "measurement", "gqm"],
            ["process", "software", "strategic"],
        ],
        n_words_per_topic=n_words_per_topic,
    )

    assert result == expected


def test_generate_search_string_with_2_similar_words_should_return_result_of_generate_search_string_with_similar_words(
    bert_similar_words_generator: BertSimilarWordsGenerator,
):
    n_words_per_topic = 2

    result = generate_search_string(
        topics=[
            ["software", "measurement", "gqm"],
            ["process", "software", "strategic"],
        ],
        n_words_per_topic=n_words_per_topic,
        n_similar_words_per_word=2,
        similar_words_generator=bert_similar_words_generator,
    )

    expected = generate_search_string_with_similar_words(
        topics=[
            ["software", "measurement", "gqm"],
            ["process", "software", "strategic"],
        ],
        n_similar_words_per_word=2,
        n_words_per_topic=n_words_per_topic,
        similar_words_generator=bert_similar_words_generator,
    )

    assert result == expected


def test_generate_search_string_should_raise_value_error_when_n_similar_words_per_word_is_greate_than_0_and_similar_words_generator_is_none():
    with pytest.raises(ValueError):
        generate_search_string(
            topics=[
                ["software", "measurement", "gqm"],
                ["process", "software", "strategic"],
            ],
            n_words_per_topic=2,
            n_similar_words_per_word=2,
            similar_words_generator=None,
        )
