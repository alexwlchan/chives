"""
pytest fixtures for working with vcrpy to record HTTP requests.

This allows us to record HTTP interactions as YAML files, so they can
be "played back" later -- e.g. in automated tests or GitHub Actions.
This means our tests are working with real responses, but don't
depend on the original service being up and running.

This establishes a couple of conventions for where cassettes are stored
and how they're named.

See https://vcrpy.readthedocs.io/
"""

from collections.abc import Iterator

import pytest
import vcr
from vcr.cassette import Cassette


__all__ = ["cassette_name", "vcr_cassette"]


def get_cassette_name(request: pytest.FixtureRequest) -> str:
    """
    Return the name of a cassette for vcr.py.

    The name can be made up of (up to) three parts:

    -   the name of the test class
    -   the name of the test function
    -   the ID of the test case in @pytest.mark.parametrize

    """
    name = request.node.name

    # This is to catch cases where e.g. we try to include a complete
    # HTTP URL in a cassette name, which creates very messy folders in
    # the fixtures directory.
    if any(char in name for char in ":/"):
        raise ValueError(
            "Illegal characters in VCR cassette name - "
            "please set a test ID with pytest.param(…, id='…')"
        )

    if request.cls is not None:
        return f"{request.cls.__name__}.{name}.yml"
    else:
        return f"{name}.yml"


@pytest.fixture
def cassette_name(request: pytest.FixtureRequest) -> str:
    """
    Return the filename of a VCR cassette to use in tests.

    This is useful when you need some custom vcr.py options, and
    can't use the prebuilt `vcr_cassette` fixture.
    """
    return get_cassette_name(request)


@pytest.fixture
def vcr_cassette(cassette_name: str) -> Iterator[Cassette]:
    """
    Create a VCR cassette for use in tests.

    Tests will record their HTTP interactions as "cassettes" using vcr.py,
    which can be replayed offline (e.g. in CI tests).
    """
    with vcr.use_cassette(
        cassette_name,
        cassette_library_dir="tests/fixtures/cassettes",
        decode_compressed_response=True,
    ) as cassette:
        yield cassette
