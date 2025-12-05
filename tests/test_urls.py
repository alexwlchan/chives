"""Tests for `chives.urls`."""

from pathlib import Path

import pytest
from vcr.cassette import Cassette

from chives.urls import (
    clean_youtube_url,
    is_mastodon_host,
    is_url_safe,
    parse_mastodon_post_url,
    parse_tumblr_post_url,
)


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


@pytest.mark.parametrize(
    "url, server, acct, post_id",
    [
        (
            "https://iconfactory.world/@Iconfactory/115650922400392083",
            "iconfactory.world",
            "Iconfactory",
            "115650922400392083",
        ),
        (
            "https://social.alexwlchan.net/@chris__martin@functional.cafe/113369395383537892",
            "functional.cafe",
            "chris__martin",
            "113369395383537892",
        ),
    ],
)
def test_parse_mastodon_post_url(
    url: str, server: str, acct: str, post_id: str
) -> None:
    """
    Mastodon post URLs are parsed correctly.
    """
    assert parse_mastodon_post_url(url) == (server, acct, post_id)


@pytest.mark.parametrize(
    "url, error",
    [
        ("https://mastodon.social/", "Cannot parse Mastodon URL"),
        ("https://mastodon.social/about", "Cannot parse Mastodon URL"),
        ("https://mastodon.social/about/subdir", "Cannot find `acct`"),
        ("https://mastodon.social/@example/about", "Mastodon post ID is not numeric"),
    ],
)
def test_parse_mastodon_post_url_errors(url: str, error: str) -> None:
    """
    parse_mastodon_post_url returns a useful error if it can't parse the URL.
    """
    with pytest.raises(ValueError, match=error):
        parse_mastodon_post_url(url)


@pytest.mark.parametrize(
    "url, blog_identifier, post_id",
    [
        (
            "https://www.tumblr.com/kynvillingur/792473255236796416/",
            "kynvillingur",
            "792473255236796416",
        ),
        (
            "https://cut3panda.tumblr.com/post/94093772689/for-some-people-the-more-you-get-to-know-them",
            "cut3panda",
            "94093772689",
        ),
    ],
)
def test_parse_tumblr_post_url(url: str, blog_identifier: str, post_id: str) -> None:
    """
    Tumblr URLs are parsed correctly.
    """
    assert parse_tumblr_post_url(url) == (blog_identifier, post_id)


class TestIsMastodonHost:
    """
    Tests for `is_mastodon_host`.
    """

    @pytest.mark.parametrize(
        "host", ["mastodon.social", "hachyderm.io", "social.jvns.ca"]
    )
    def test_mastodon_servers(self, host: str, vcr_cassette: Cassette) -> None:
        """
        It correctly identifies real Mastodon servers.
        """
        assert is_mastodon_host(host)

    @pytest.mark.parametrize(
        "host",
        [
            # These are regular Internet websites which don't expose
            # the /.well-known/nodeinfo endpoint
            "example.com",
            "alexwlchan.net",
            #
            # PeerTube exposes /.well-known/nodeinfo, but it's running
            # different software.
            "peertube.tv",
        ],
    )
    def test_non_mastodon_servers(self, host: str, vcr_cassette: Cassette) -> None:
        """
        Other websites are not Mastodon servers.
        """
        assert not is_mastodon_host(host)


class TestIsUrlSafe:
    """
    Tests for `is_url_safe`.
    """

    @pytest.mark.parametrize("path", ["example.txt", Path("a/b/cat.jpg")])
    def test_safe(self, path: str | Path) -> None:
        """Paths which are URL safe."""
        assert is_url_safe(path)

    @pytest.mark.parametrize("path", ["is it?", Path("cat%c.jpg"), "a#b"])
    def test_unsafe(self, path: str | Path) -> None:
        """Paths which are not URL safe."""
        assert not is_url_safe(path)
