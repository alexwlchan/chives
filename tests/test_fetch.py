"""
Tests for `chives.fetch`.
"""

from io import BytesIO
import json
from typing import Any
from urllib.error import HTTPError

from PIL import Image
import pytest
import vcr
from vcr.cassette import Cassette

from chives.fetch import fetch_image, fetch_url


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


class TestFetchImage:
    """
    Tests for `fetch_image`.
    """

    def test_http_200(self, vcr_cassette: Cassette) -> None:
        """
        Fetch an image and check we get the correct format.
        """
        url = "https://api.tumblr.com/v2/blog/thecroissantgirl.tumblr.com/avatar"

        img_data, img_format = fetch_image(url)
        assert img_format == "png"

        im = Image.open(BytesIO(img_data))
        assert im.format == "PNG"

    def test_non_image(self, vcr_cassette: Cassette) -> None:
        """
        Fetching an "image" which has a non-image Content-Type header
        throws an error.
        """
        url = "http://httpbin.org/status/200"

        with pytest.raises(RuntimeError, match="unrecognised image format"):
            fetch_image(url)

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
                fetch_image(url)
