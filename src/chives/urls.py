"""Code for manipulating and tidying URLs."""

import json
from pathlib import Path
import re
import ssl
from ssl import SSLCertVerificationError
import urllib.error
from urllib.error import HTTPError
from urllib.parse import SplitResult, parse_qs, urlencode, urlsplit
import urllib.request

import certifi

from chives.fetch import fetch_url


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
    u = urlsplit(url)

    query = parse_qs(u.query)
    for param in ("list", "index", "start_radio", "t"):
        try:
            del query[param]
        except KeyError:
            pass

    updated_u = SplitResult(
        scheme=u.scheme,
        netloc=u.netloc,
        path=u.path,
        query=urlencode(query, doseq=True),
        fragment=u.fragment,
    )

    return updated_u.geturl()


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
    u = urlsplit(url)
    path = u.path.strip("/").split("/")

    if len(path) != 2:
        raise ValueError("Cannot parse Mastodon URL!")

    if not path[0].startswith("@"):
        raise ValueError("Cannot find `acct` in Mastodon URL!")

    if not re.fullmatch(r"^[0-9]+$", path[1]):
        raise ValueError("Mastodon post ID is not numeric!")

    if u.netloc == "social.alexwlchan.net" and path[0] != "@alex":
        _, acct, server = path[0].split("@")
        html = fetch_url(url).decode("utf8")
        if m := re.search(
            f'<a rel="noopener" href="https://{server}/@{acct}/(?P<post_id>[0-9]+)">',
            html,
        ):
            post_id = m.group("post_id")
            return server, acct, post_id
        else:
            raise ValueError("Cannot parse Mastodon URL!")

    server = u.netloc
    acct = path[0].replace("@", "")
    post_id = path[1]

    return server, acct, post_id


def parse_tumblr_post_url(url: str) -> tuple[str, str]:
    """
    Parse a Tumblr URL into its component parts.

    Returns a tuple (blog_identifier, post ID).
    """
    u = urlsplit(url)
    path = u.path.strip("/").split("/")

    if u.netloc == "www.tumblr.com" and len(path) >= 2:
        return path[0], path[1]

    elif u.netloc.endswith(".tumblr.com") and len(path) >= 3 and path[0] == "post":
        return u.netloc.replace(".tumblr.com", ""), path[1]

    else:
        raise ValueError("Cannot parse Tumblr URL!")


def is_url_safe(path: str | Path) -> bool:
    """
    Return True if a path is safe to use in a URL, False otherwise.
    """
    p = str(path)
    return not ("?" in p or "#" in p or "%" in p)
