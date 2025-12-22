"""
Functions for interacting with timestamps and date strings.

References:
* https://alexwlchan.net/2025/messy-dates-in-json/

"""

from collections.abc import Iterable, Iterator
from datetime import datetime, timezone
from typing import Any


def now() -> str:
    """
    Returns the current time in the standard format used by my static sites.
    """
    return (
        datetime.now(tz=timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def find_all_dates(json_value: Any) -> Iterator[tuple[dict[str, Any], str, str]]:
    """
    Find all the timestamps in a heavily nested JSON object.

    This function looks for any JSON objects with a key-value pair
    where the key starts with `date_` and the value is a string, and
    emits a 3-tuple:

    *   the JSON object
    *   the key
    *   the value

    """
    if isinstance(json_value, dict):
        for key, value in json_value.items():
            if (
                isinstance(key, str)
                and key.startswith("date_")
                and isinstance(value, str)
            ):
                yield json_value, key, value
            else:
                yield from find_all_dates(value)
    elif isinstance(json_value, list):
        for value in json_value:
            yield from find_all_dates(value)


def date_matches_format(date_string: str, format: str) -> bool:
    """
    Returns True if `date_string` can be parsed as a datetime
    using `format`, False otherwise.
    """
    try:
        datetime.strptime(date_string, format)
        return True
    except ValueError:
        return False


def date_matches_any_format(date_string: str, formats: Iterable[str]) -> bool:
    """
    Returns True if `date_string` can be parsed as a datetime
    with any of the `formats`, False otherwise.
    """
    return any(date_matches_format(date_string, fmt) for fmt in formats)


def reformat_date(s: str, /, orig_fmt: str) -> str:
    """
    Reformat a date to one of my desired formats.
    """
    if "%Z" in orig_fmt:
        d = datetime.strptime(s, orig_fmt)
    else:
        d = datetime.strptime(s.replace("Z", "+0000"), orig_fmt.replace("Z", "%z"))
    d = d.replace(microsecond=0)
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    else:
        d = d.astimezone(tz=timezone.utc)
    return d.strftime("%Y-%m-%dT%H:%M:%S%z").replace("+0000", "Z")
