"""Code for manipulating and tidying URLs."""

import json
from pathlib import Path
import re
import ssl
from ssl import SSLCertVerificationError
import urllib.error
from urllib.error import HTTPError
import urllib.request

import certifi


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
    u = u.remove("start_radio")
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

    ssl_context = ssl.create_default_context(cafile=certifi.where())

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
    nodeinfo_url = f"https://{hostname}/.well-known/nodeinfo"

    try:
        nodeinfo_resp = urllib.request.urlopen(nodeinfo_url, context=ssl_context)
    except HTTPError as err:
        err.close()
        return False
    except SSLCertVerificationError:
        return False

    nodeinfo = json.loads(nodeinfo_resp.read())
    nodeinfo_resp.close()

    # Then we try to call $.links[0].href, which should return something
    # like:
    #
    #     {
    #       "version": "2.0",
    #       "software": {"name": "mastodon", "version": "4.5.2"},
    #       …
    #
    try:
        link_href = nodeinfo["links"][0]["href"]
    except (KeyError, IndexError):  # pragma: no cover
        return False

    link_resp = urllib.request.urlopen(link_href, context=ssl_context)
    link_info = json.loads(link_resp.read())
    link_resp.close()

    try:
        return bool(link_info["software"]["name"] == "mastodon")
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
