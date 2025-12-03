# CHANGELOG

## v7 - 2025-12-03

Add the `parse_tumblr_post_url()` function.

## v6 - 2025-12-03

Add the `parse_mastodon_post_url()` function.

## v5 - 2025-12-01

When calling `reformat_date()`, ensure all dates are converted to UTC.

## v4 - 2025-11-29

Rename `chives.timestamps` to `chives.dates`.

## v3 - 2025-11-29

Add the `clean_youtube_url()` function and `urls` extra.
Rearrange the package structure slightly, to allow optional dependencies.

## v2 - 2025-11-28

Add the `is_av1_video()` function for [detecting AV1-encoded videos](https://alexwlchan.net/2025/detecting-av1-videos/).

## v1 - 2025-11-28

Initial release. Included functions:

* `date_matches_any_format`
* `date_matches_format`
* `find_all_dates`
* `reformat_date`
