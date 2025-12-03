"""Code for manipulating and tidying URLs."""

import re
from typing import TypedDict

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


def parse_mastodon_post_url(url: str) -> tuple[str, str, str]:
    """
    Parse a Mastodon post URL into its component parts:
    server, account, post ID.
    """
    u = hyperlink.parse(url)

    if len(u.path) != 2:
        raise ValueError("Cannot parse Mastodon URL!")

    if not u.path[0].startswith("@"):
        raise ValueError("Cannot find `acct` in Mastodon URL!")

    if not re.fullmatch(r"^[0-9]+$", u.path[1]):
        raise ValueError("Mastodon post ID is not numeric!")

    if u.host == "social.alexwlchan.net":
        _, acct, server = u.path[0].split("@")
    else:
        server = u.host
        acct = u.path[0].replace("@", "")

    return server, acct, u.path[1]
