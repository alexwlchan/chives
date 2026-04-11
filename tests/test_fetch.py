"""
Tests for `chives.fetch`.
"""

import filecmp
import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError

import pytest
import vcr
from vcr.cassette import Cassette

from chives.fetch import build_request, download_image, fetch_url, QueryParams


@pytest.mark.parametrize(
    "url, params, expected_url",
    [
        ("https://example.com", None, "https://example.com"),
        (
            "https://example.com",
            {"one": "1", "two": "2"},
            "https://example.com?one=1&two=2",
        ),
        (
            "https://example.com",
            [("one", "1"), ("two", "2")],
            "https://example.com?one=1&two=2",
        ),
        (
            "https://example.com",
            [("num", "1"), ("num", "2")],
            "https://example.com?num=1&num=2",
        ),
        (
            "https://example.com#fragment",
            [("num", "1"), ("num", "2")],
            "https://example.com?num=1&num=2#fragment",
        ),
        (
            "https://example.com?existing=1",
            [("num", "1"), ("num", "2")],
            "https://example.com?existing=1&num=1&num=2",
        ),
        (
            "https://example.com?existing=1#fragment",
            [("num", "1"), ("num", "2")],
            "https://example.com?existing=1&num=1&num=2#fragment",
        ),
    ],
)
def test_build_request(url: str, params: QueryParams | None, expected_url: str) -> None:
    """
    Tests for `build_request`.
    """
    req = build_request(url, params=params)
    assert req.full_url == expected_url


class TestFetchUrl:
    """
    Tests for `fetch_url`.
    """

    def test_http_200(self, vcr_cassette: Cassette) -> None:
        """
        Fetch a URL and check we get the expected response body.
        """
        resp = fetch_url("http://httpbin.org/robots.txt")
        assert resp == b"User-agent: *\nDisallow: /deny\n"

    def test_http_404(self, vcr_cassette: Cassette) -> None:
        """
        Fetch a URL that returns a 404 Not Found error.
        """
        with pytest.raises(HTTPError) as exc:
            fetch_url("http://httpbin.org/status/404")

        assert exc.value.code == 404
        exc.value.close()

    def test_query_params(self, vcr_cassette: Cassette) -> None:
        """
        Pass some query parameters in the fetch request.
        """
        resp = fetch_url(
            "http://httpbin.org/get",
            params={"package": "chives", "author": "alexwlchan"},
        )

        args = json.loads(resp)["args"]

        assert args["package"] == "chives"
        assert args["author"] == "alexwlchan"

    def test_headers(self, vcr_cassette: Cassette) -> None:
        """
        Pass some headers in the fetch request.
        """
        resp = fetch_url(
            "http://httpbin.org/headers",
            headers={"X-Package": "chives", "X-Author": "alexwlchan"},
        )

        headers = json.loads(resp)["headers"]

        assert headers["X-Package"] == "chives"
        assert headers["X-Author"] == "alexwlchan"


class TestDownloadImage:
    """
    Tests for `download_image`.
    """

    def test_download_image(self, tmp_path: Path, vcr_cassette: Cassette) -> None:
        """
        Download an image and compare the result.
        """
        url = "https://alexwlchan.net/images/2026/470906.png"

        out_path = download_image(url, tmp_path / "470906")
        assert out_path == tmp_path / "470906.png"
        assert out_path.exists()

        assert filecmp.cmp(out_path, "tests/fixtures/media/470906.png", shallow=False)

    def test_download_to_nested_path(
        self, tmp_path: Path, vcr_cassette: Cassette
    ) -> None:
        """
        You can download an image to a heavily nested path, and it creates
        the parent directory.
        """
        url = "https://alexwlchan.net/images/2026/470906.png"

        out_path = download_image(url, tmp_path / "a/b/c/470906")
        assert out_path == tmp_path / "a/b/c/470906.png"
        assert out_path.exists()

        assert filecmp.cmp(out_path, "tests/fixtures/media/470906.png", shallow=False)

    def test_cannot_download_twice(
        self, tmp_path: Path, vcr_cassette: Cassette
    ) -> None:
        """
        Trying to overwrite an existing image throws a FileExistsError.
        """
        url1 = "https://alexwlchan.net/images/2026/470906.png"
        url2 = "https://alexwlchan.net/images/2026/f69b96.png"

        out_path = download_image(url1, tmp_path / "squares")
        assert filecmp.cmp(out_path, "tests/fixtures/media/470906.png", shallow=False)

        with pytest.raises(FileExistsError):
            download_image(url2, tmp_path / "squares")

        # The file contents are the same as the first download.
        assert filecmp.cmp(out_path, "tests/fixtures/media/470906.png", shallow=False)

    def test_non_image(self, vcr_cassette: Cassette) -> None:
        """
        Fetching an "image" which has a non-image Content-Type header
        throws an error.
        """
        url = "http://httpbin.org/status/200"

        with pytest.raises(ValueError, match="unrecognised image format"):
            download_image(url, out_prefix=Path("example"))

    def test_no_content_type_header(self, cassette_name: str) -> None:
        """
        Fetching a URL which doesn't return a Content-Type header
        throws an error.
        """
        url = "http://httpbin.org/status/200"

        def delete_content_type_header(response: Any) -> Any:
            response["headers"]["Content-Type"] = []
            return response

        with vcr.use_cassette(
            cassette_name,
            cassette_library_dir="tests/fixtures/cassettes",
            decode_compressed_response=True,
            before_record_response=delete_content_type_header,
        ):
            with pytest.raises(
                RuntimeError, match="no Content-Type header in response"
            ):
                download_image(url, out_prefix=Path("example"))
