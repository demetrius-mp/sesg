from sesg.snowballing import fuzzy_bsb


def test_check_title_is_in_text_should_return_true_when_title_is_in_study():
    # arrange
    study = "something something here goes a reference: machine learning applied in biomechanics: a systematic literature review."
    title = "machine learning applied in biomechanics: a systematic literature review."

    expected = True

    # act
    result = fuzzy_bsb.check_title_is_in_text(
        text=study,
        title=title,
    )

    # assert
    assert result == expected


def test_check_title_is_in_text_should_return_true_when_title_is_similar_to_some_text_in_study():
    # arrange
    study = "something something here goes a reference: machine learning applied in biomechanics: a systematic literature review."
    title = "Machine learning applied in biomechanics, a systematic literature review."

    expected = True

    # act
    result = fuzzy_bsb.check_title_is_in_text(
        text=study,
        title=title,
    )

    # assert
    assert result == expected


def test_check_title_is_in_text_should_return_false_when_title_is_not_in_study():
    # arrange
    study = "something something here goes a reference: machine learning applied in biomechanics: a systematic literature review."
    title = (
        "Machine learning in aerospacial engineering: A systematic literature review."
    )

    expected = False

    # act
    result = fuzzy_bsb.check_title_is_in_text(
        text=study,
        title=title,
    )

    # assert
    assert result == expected


def test_pooled_check_title_is_in_text_should_return_false_when_skip_is_true():
    # arrange
    text = "something something here goes a reference: machine learning applied in biomechanics: a systematic literature review."
    title = "machine learning applied in biomechanics: a systematic literature review."

    expected = False

    # act
    result = fuzzy_bsb.pooled_check_title_is_in_text(
        {
            "text": text,
            "title": title,
            "skip": True,
        }
    )

    # assert
    assert result == expected


def test_pooled_check_title_is_in_text_should_return_false_when_skip_is_true_even_if_the_study_cites_the_title():
    # arrange
    text = "something something here goes a reference: machine learning applied in biomechanics: a systematic literature review."
    title = "machine learning applied in biomechanics: a systematic literature review."
    title_is_in_text = fuzzy_bsb.check_title_is_in_text(
        text=text,
        title=title,
    )

    expected = False

    # act
    result = fuzzy_bsb.pooled_check_title_is_in_text(
        {
            "text": text,
            "title": title,
            "skip": True,
        }
    )

    # assert
    assert title_is_in_text is True
    assert result == expected


def test_pooled_check_title_is_in_text_should_return_result_of_study_cites_title_when_skip_is_false():
    # arrange
    text = "something something here goes a reference: machine learning applied in biomechanics: a systematic literature review."
    title = "machine learning applied in biomechanics: a systematic literature review."

    expected = fuzzy_bsb.check_title_is_in_text(
        text=text,
        title=title,
    )

    # act
    result = fuzzy_bsb.pooled_check_title_is_in_text(
        {
            "text": text,
            "title": title,
            "skip": False,
        }
    )

    # assert
    assert result == expected


def test_preprocess_title_should_strip_string_turn_to_lower_case_remove_spaces_and_dots():
    # arrange
    value = "  leading whitespace .dots   spaces UPPERCASE trailing whitespaces   "

    expected = "leadingwhitespacedotsspacesuppercasetrailingwhitespaces"

    # act
    result = fuzzy_bsb.preprocess_title(value)

    assert result == expected


def test_preprocess_title_should_not_remove_special_characters():
    # arrange
    value = "  leading whitespace .dots   spaces UPPERCASE trailing whitespaces"
    special_characters = "string,<>;:/?~^'`[{()}]!@#$%&*-_=+'\""

    expected = "leadingwhitespacedotsspacesuppercasetrailingwhitespaces" + special_characters  # fmt: skip

    # act
    result = fuzzy_bsb.preprocess_title(value + special_characters + "  ")

    assert result == expected


def test_preprocess_text_should_strip_string_turn_to_lower_case_remove_spaces_dots_line_breaks_and_line_carriages():
    # arrange
    value = "  leading whitespace .dots   spaces UPPERCASE \n line break \r line carriage trailing whitespaces   "

    expected = "leadingwhitespacedotsspacesuppercaselinebreaklinecarriagetrailingwhitespaces"  # fmt: skip

    # act
    result = fuzzy_bsb.preprocess_text(value)

    assert result == expected


def test_preprocess_text_should_not_remove_special_characters():
    # arrange
    value = "  leading whitespace .dots   spaces UPPERCASE \n line break \r line carriage trailing whitespaces"
    special_characters = "string,<>;:/?~^'`[{()}]!@#$%&*-_=+'\""

    expected = "leadingwhitespacedotsspacesuppercaselinebreaklinecarriagetrailingwhitespaces" + special_characters  # fmt: skip

    # act
    result = fuzzy_bsb.preprocess_text(value + special_characters + "  ")

    assert result == expected


def test_snowballing_study_instance_should_have_preprocessed_title_and_text_content():
    # arrange
    title = "  title HERE. ,  "
    text_content = " text CONTENT \r\n ,.. test "

    preprocessed_title = fuzzy_bsb.preprocess_title(title)
    preprocessed_text_content = fuzzy_bsb.preprocess_text(text_content)

    # act
    snowballing_study = fuzzy_bsb.FuzzyBackwardSnowballingStudy(
        id=1,
        text_content=text_content,
        title=title,
    )

    assert snowballing_study.title == preprocessed_title
    assert snowballing_study.text_content == preprocessed_text_content
