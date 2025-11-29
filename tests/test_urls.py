"""Tests for `chives.urls`."""

import pytest

from chives.urls import clean_youtube_url


@pytest.mark.parametrize(
    "url, cleaned_url",
    [
        (
            "https://www.youtube.com/watch?v=2OHPPSew2nY&list=WL&index=6&t=193s",
            "https://www.youtube.com/watch?v=2OHPPSew2nY",
        ),
        (
            "https://www.youtube.com/watch?v=2OHPPSew2nY",
            "https://www.youtube.com/watch?v=2OHPPSew2nY",
        ),
    ],
)
def test_clean_youtube_url(url: str, cleaned_url: str) -> None:
    """
    All the query parameters get stripped from YouTube URLs correctly.
    """
    assert clean_youtube_url(url) == cleaned_url
