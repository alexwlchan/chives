"""
Functions for dealing with text.
"""

import functools

import smartypants


@functools.cache
def smartify(text: str) -> str:
    """
    Add curly quotes and smart dashes to a string.
    """
    # Undo some escaping from Mistune.
    text = text.replace("&quot;", '"')

    attrs = (
        # normal quotes (" and ') to curly ones
        smartypants.Attr.q
        |
        # typewriter dashes (--) to en-dashes and dashes (---) to em-dashes
        smartypants.Attr.D
        |
        # dashes (...) to ellipses
        smartypants.Attr.e
        |
        # output Unicode chars instead of numeric character references
        smartypants.Attr.u
    )

    return smartypants.smartypants(text, attrs)
