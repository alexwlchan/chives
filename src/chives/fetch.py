"""
Make HTTP requests using the standard library.
"""

import ssl
from typing import Literal
import urllib.parse
import urllib.request

import certifi


__all__ = ["fetch_url", "fetch_image", "ImageFormat"]


def _build_request(
    url: str, params: dict[str, str] | None, headers: dict[str, str] | None
) -> urllib.request.Request:
    """
    Build a request based on the given inputs.
    """
    if params:
        params_str = urllib.parse.urlencode(params)
        url = url + "?" + params_str

    req = urllib.request.Request(url)

    if headers:
        for name, value in headers.items():
            req.add_header(name, value)

    return req


def fetch_url(
    url: str,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> bytes:
    """
    Fetch the contents of the given URL and return the body of
    the response.
    """
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    req = _build_request(url, params, headers)

    resp = urllib.request.urlopen(req, context=ssl_context)

    data = resp.read()
    resp.close()
    assert isinstance(data, bytes), type(data)

    return data


ImageFormat = Literal["jpg", "png", "gif", "webp"]


def _guess_image_format(content_type: str | None) -> ImageFormat:
    """
    Given the Content-Type response header, guess the image format.
    """
    if content_type is None:
        raise RuntimeError(
            "no Content-Type header in response, cannot guess image format"
        )

    content_type_mapping: dict[str, ImageFormat] = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/gif": "gif",
        "image/webp": "webp",
    }

    try:
        return content_type_mapping[content_type]
    except KeyError:
        raise RuntimeError(f"unrecognised image format: {content_type}")


def fetch_image(
    url: str,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[bytes, ImageFormat]:
    """
    Fetch an image from the given URL and return the image data and
    image format.
    """
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    req = _build_request(url, params, headers)

    resp = urllib.request.urlopen(req, context=ssl_context)

    img_format = _guess_image_format(content_type=resp.headers["content-type"])

    img_data = resp.read()
    resp.close()
    assert isinstance(img_data, bytes), type(img_data)

    return img_data, img_format
