"""Code for manipulating and tidying URLs."""

import hyperlink


def clean_youtube_url(url: str) -> str:
    """
    Remove any query parameters from a YouTube URL that I don't
    want to include.
    """
    u = hyperlink.parse(url)

    u = u.remove("list")
    u = u.remove("index")
    u = u.remove("t")

    return str(u)
