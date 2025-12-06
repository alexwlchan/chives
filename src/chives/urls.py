"""Code for manipulating and tidying URLs."""

from pathlib import Path
import re


__all__ = [
    "clean_youtube_url",
    "is_mastodon_host",
    "is_url_safe",
    "parse_mastodon_post_url",
    "parse_tumblr_post_url",
]


def clean_youtube_url(url: str) -> str:
    """
    Remove any query parameters from a YouTube URL that I don't
    want to include.
    """
    import hyperlink

    u = hyperlink.parse(url)

    u = u.remove("list")
    u = u.remove("index")
    u = u.remove("t")

    return str(u)


def is_mastodon_host(hostname: str) -> bool:
    """
    Check if a hostname is a Mastodon server.
    """
    if hostname in {
        "hachyderm.io",
        "iconfactory.world",
        "mas.to",
        "mastodon.social",
        "social.alexwlchan.net",
    }:
        return True

    # See https://github.com/mastodon/mastodon/discussions/30547
    #
    # Fist we look at /.well-known/nodeinfo, which returns a response
    # like this for Mastodon servers:
    #
    #     {
    #       "links": [
    #         {
    #           "rel": "http://nodeinfo.diaspora.software/ns/schema/2.0",
    #           "href": "https://mastodon.online/nodeinfo/2.0"
    #         }
    #       ]
    #     }
    #
    import httpx

    nodeinfo_resp = httpx.get(f"https://{hostname}/.well-known/nodeinfo")
    try:
        nodeinfo_resp.raise_for_status()
    except Exception:
        return False

    # Then we try to call $.links[0].href, which should return something
    # like:
    #
    #     {
    #       "version": "2.0",
    #       "software": {"name": "mastodon", "version": "4.5.2"},
    #       …
    #
    try:
        href = nodeinfo_resp.json()["links"][0]["href"]
    except (KeyError, IndexError):  # pragma: no cover
        return False

    link_resp = httpx.get(href)
    try:
        link_resp.raise_for_status()
    except Exception:  # pragma: no cover
        return False

    try:
        return bool(link_resp.json()["software"]["name"] == "mastodon")
    except (KeyError, IndexError):  # pragma: no cover
        return False


def parse_mastodon_post_url(url: str) -> tuple[str, str, str]:
    """
    Parse a Mastodon post URL into its component parts:
    server, account, post ID.
    """
    import hyperlink

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


def parse_tumblr_post_url(url: str) -> tuple[str, str]:
    """
    Parse a Tumblr URL into its component parts.

    Returns a tuple (blog_identifier, post ID).
    """
    import hyperlink

    u = hyperlink.parse(url)

    if u.host == "www.tumblr.com":
        return u.path[0], u.path[1]

    if u.host.endswith(".tumblr.com") and len(u.path) >= 3 and u.path[0] == "post":
        return u.host.replace(".tumblr.com", ""), u.path[1]

    raise ValueError("Cannot parse Tumblr URL!")  # pragma: no cover


def is_url_safe(path: str | Path) -> bool:
    """
    Returns True if a path is safe to use in a URL, False otherwise.
    """
    p = str(path)
    return not ("?" in p or "#" in p or "%" in p)
