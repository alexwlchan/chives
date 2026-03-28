"""
Tests for `cassettes`.
"""

import pytest
from vcr.cassette import Cassette

from cassettes import get_cassette_name


def test_creates_cassette(cassette_name: str) -> None:
    """
    The filename of a VCR cassette is the test name, plus a YAML extension.
    """
    assert cassette_name == "test_creates_cassette.yml"


@pytest.mark.parametrize(
    ["expected_cassette_name"],
    [
        pytest.param("test_creates_parametrized_cassette[test1].yml", id="test1"),
        pytest.param("test_creates_parametrized_cassette[test2].yml", id="test2"),
        pytest.param("test_creates_parametrized_cassette[test3].yml", id="test3"),
    ],
)
def test_creates_parametrized_cassette(
    cassette_name: str, expected_cassette_name: str
) -> None:
    """
    In a parametrized test, the filename of the VCR cassette includes
    the test case name in square brackets.
    """
    assert cassette_name == expected_cassette_name


class TestCassetteNameInClass:
    """
    TestCassetteNameInClass exists so the next test can run inside
    a class, simulating how tests are often organised in "real" test suites.
    """

    def test_prefixes_class_name_to_cassette(self, cassette_name: str) -> None:
        """
        In a test in a class, the filename of the VCR cassette includes
        the class name as a prefix.
        """
        assert (
            cassette_name
            == "TestCassetteNameInClass.test_prefixes_class_name_to_cassette.yml"
        )

    @pytest.mark.parametrize(
        ["expected_cassette_name"],
        [
            pytest.param(
                "TestCassetteNameInClass.test_prefixes_name_with_parametrized_cassette[test1].yml",
                id="test1",
            ),
            pytest.param(
                "TestCassetteNameInClass.test_prefixes_name_with_parametrized_cassette[test2].yml",
                id="test2",
            ),
            pytest.param(
                "TestCassetteNameInClass.test_prefixes_name_with_parametrized_cassette[test3].yml",
                id="test3",
            ),
            pytest.param(
                "TestCassetteNameInClass.test_prefixes_name_with_parametrized_cassette[test.name.with.periods].yml",
                id="test.name.with.periods",
            ),
        ],
    )
    def test_prefixes_name_with_parametrized_cassette(
        self, cassette_name: str, expected_cassette_name: str
    ) -> None:
        """
        In a parametrized test in a class, the filename of the
        VCR cassette includes the class name as a prefix and the
        test case name as a suffix.
        """
        assert cassette_name == expected_cassette_name


@pytest.mark.parametrize("url", ["https://example.com"])
def test_throws_if_bad_cassette_name(url: str, request: pytest.FixtureRequest) -> None:
    """
    Trying to use a URL as a VCR cassette name throws a ``ValueError``.
    """
    with pytest.raises(ValueError, match="Illegal characters in VCR cassette name"):
        get_cassette_name(request)


def test_creates_cassette_in_fixture_dir(vcr_cassette: Cassette) -> None:
    """
    The VCR cassette is created in the ``tests/fixtures/cassettes`` directory.
    """
    assert (
        vcr_cassette._path
        == "tests/fixtures/cassettes/test_creates_cassette_in_fixture_dir.yml"
    )
