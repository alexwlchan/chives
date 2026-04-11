"""
Make HTTP requests using the standard library.
"""

from pathlib import Path
import ssl
from typing import Literal
import urllib.parse
import urllib.request

import certifi


__all__ = ["build_request", "download_image", "fetch_url"]


ssl_context = ssl.create_default_context(cafile=certifi.where())

QueryParams = dict[str, str] | list[tuple[str, str]]
Headers = dict[str, str]


def build_request(
    url: str, *, params: QueryParams | None = None, headers: Headers | None = None
) -> urllib.request.Request:
    """
    Build a request based on the given inputs.
    """
    if isinstance(params, dict):
        params = [(k, v) for k, v in params.items()]
    if params is not None:
        u = urllib.parse.urlsplit(url)
        query = urllib.parse.parse_qsl(u.query) + params
        new_query = urllib.parse.urlencode(query)
        url = urllib.parse.urlunsplit(
            (u.scheme, u.netloc, u.path, new_query, u.fragment)
        )

    req = urllib.request.Request(url)

    if headers:
        for name, value in headers.items():
            req.add_header(name, value)

    return req


def fetch_url(
    url: str, *, params: QueryParams | None = None, headers: Headers | None = None
) -> bytes:
    """
    Fetch the contents of the given URL and return the body of
    the response.
    """
    req = build_request(url, params=params, headers=headers)

    with urllib.request.urlopen(req, context=ssl_context) as resp:
        data = resp.read()

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
        raise ValueError(f"unrecognised image format: {content_type}")


def download_image(
    url: str,
    out_prefix: Path,
    *,
    params: QueryParams | None = None,
    headers: Headers | None = None,
) -> Path:
    """
    Download an image from the given URL to the target path, and return
    the path of the downloaded file.

    Add the appropriate file extension, based on the image's Content-Type.

    Throws a FileExistsError if you try to overwrite an existing file.
    """
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    req = build_request(url, params=params, headers=headers)

    with urllib.request.urlopen(req, context=ssl_context) as resp:
        img_data = resp.read()
        assert isinstance(img_data, bytes), type(img_data)

    img_format = _guess_image_format(content_type=resp.headers["content-type"])

    out_path = out_prefix.with_suffix("." + img_format)

    out_path.parent.mkdir(exist_ok=True, parents=True)

    with open(out_path, "xb") as out_file:
        out_file.write(img_data)

    return out_path
