import pytest
from sesg.search_string import InvalidPubyearBoundariesError, set_pub_year_boundaries


@pytest.mark.parametrize(
    "string,min_year,max_year,expected",
    [
        ("nlp", 1999, 2018, "nlp AND PUBYEAR > 1999 AND PUBYEAR < 2018"),
        ("nlp", 1999, None, "nlp AND PUBYEAR > 1999"),
        ("nlp", None, 2018, "nlp AND PUBYEAR < 2018"),
    ],
)
def test_set_pubyear_boundaries(
    string,
    min_year,
    max_year,
    expected,
):
    value = set_pub_year_boundaries(
        string=string,
        min_year=min_year,
        max_year=max_year,
    )

    assert value == expected


def test_set_pubyear_boundaries_should_raise_exception_when_min_year_is_greater_than_max_year():
    with pytest.raises(InvalidPubyearBoundariesError):
        set_pub_year_boundaries(
            string="string",
            min_year=2018,
            max_year=1999,
        )
