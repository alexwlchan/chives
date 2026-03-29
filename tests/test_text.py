"""
Tests for `chives.text`.
"""

import pytest

from chives.text import smartify


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Isn't it delightful -- she said", "Isn’t it delightful – she said"),
        ("Are you ... sure?", "Are you … sure?"),
        ("<h2>Isn't it delightful?</h2>", "<h2>Isn’t it delightful?</h2>"),
        ("<li>Isn't it delightful?</li>", "<li>Isn’t it delightful?</li>"),
        ("<p>&quot;It's nice&quot;, he said</p>", "<p>“It’s nice”, he said</p>"),
    ],
)
def test_smartify(text: str, expected: str) -> None:
    """
    Test smartify().
    """
    actual = smartify(text)
    assert actual == expected
