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
    attrs = (
        # normal quotes (" and ') to curly ones
        smartypants.Attr.q
        |
        # quote entities (&quot;) to curly quotes
        smartypants.Attr.w
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
