"""
chives is a collection of Python functions for working with my local
media archives.

I store a lot of media archives as static websites [1][2], and I use
Python scripts to manage my media. This package has some functions
I share across multiple sites.

[1]: https://alexwlchan.net/2024/static-websites/
[2]: https://alexwlchan.net/2025/mildly-dynamic-websites/

"""

from .media import is_av1_video
from .timestamps import (
    find_all_dates,
    date_matches_format,
    date_matches_any_format,
    reformat_date,
)

__version__ = "2"

__all__ = [
    "date_matches_any_format",
    "date_matches_format",
    "find_all_dates",
    "is_av1_video",
    "reformat_date",
]
