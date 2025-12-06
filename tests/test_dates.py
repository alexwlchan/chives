"""Tests for `chives.dates`."""

import json

import pytest

from chives.dates import date_matches_any_format, find_all_dates, reformat_date


def test_find_all_dates() -> None:
    """find_all_dates finds all the nested dates in a JSON object."""
    json_value = json.loads("""{
      "doc1": {"id": "1", "date_created": "2025-10-14T05:34:07+0000"},
      "shapes": [
        {"color": "blue", "date_saved": "2015-03-01 23:34:39 +00:00"},
        {"color": "yellow", "date_saved": "2013-9-21 13:43:00Z", "is_square": true},
        {"color": "green", "date_saved": null}
      ],
      "date_verified": "2024-08-30"
    }""")

    assert list(find_all_dates(json_value)) == [
        (
            {"id": "1", "date_created": "2025-10-14T05:34:07+0000"},
            "date_created",
            "2025-10-14T05:34:07+0000",
        ),
        (
            {"color": "blue", "date_saved": "2015-03-01 23:34:39 +00:00"},
            "date_saved",
            "2015-03-01 23:34:39 +00:00",
        ),
        (
            {"color": "yellow", "date_saved": "2013-9-21 13:43:00Z", "is_square": True},
            "date_saved",
            "2013-9-21 13:43:00Z",
        ),
        (json_value, "date_verified", "2024-08-30"),
    ]


def test_date_matches_any_format() -> None:
    """
    Tests for `date_matches_any_format`.
    """
    assert date_matches_any_format(
        "2001-01-01", formats=["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z"]
    )
    assert not date_matches_any_format("2001-01-01", formats=["%Y-%m-%dT%H:%M:%S%z"])


@pytest.mark.parametrize(
    "s, orig_fmt, formatted_date",
    [
        ("2025-11-12T15:34:39.570Z", "%Y-%m-%dT%H:%M:%S.%fZ", "2025-11-12T15:34:39Z"),
        ("2025-03-12 09:57:03", "%Y-%m-%d %H:%M:%S", "2025-03-12T09:57:03Z"),
        ("2016-02-25 05:28:35 GMT", "%Y-%m-%d %H:%M:%S %Z", "2016-02-25T05:28:35Z"),
        ("2011-12-06T10:45:15-08:00", "%Y-%m-%dT%H:%M:%S%z", "2011-12-06T18:45:15Z"),
    ],
)
def test_reformat_date(s: str, orig_fmt: str, formatted_date: str) -> None:
    """Tests for `reformat_date`."""
    assert reformat_date(s, orig_fmt) == formatted_date
