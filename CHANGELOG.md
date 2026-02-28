# CHANGELOG

## v25 - 2026-02-28

Change the type of `StaticSiteTestSuite.pages_to_check` from `set` to `list` to ensure consistent ordering of parametrised tests.

Fix a bug when testing URLs with query parameters.

## v24 - 2026-02-28

In `StaticSiteTestSuite`, add testing with [Playwright](https://playwright.dev) that checks static websites render correctly.

**Breaking change:** the site root must now be specified as a classmethod `get_site_root()` rather than a `site_root` fixture.

## v23 - 2026-02-20

Change the format of `VideoEntity.subtitles` to be a list of `SubtitlesEntity`, so a single video can have multiple subtitles.

## v22 - 2026-01-11

Remove the `start_radio` parameter in `clean_youtube_url()`.

## v21 - 2025-12-22

Add a method `dates.now()` to return the current time in the timestamp used by all my static sites.

## v20 - 2025-12-10

Use concurrency in `test_no_videos_are_av1`, which can make it faster for
larger media collections.

## v19 - 2025-12-09

Allow passing both `width` and `height` as part of `ThumbnailConfig`, to constrain a thumbnail to a bounding box.

## v18 - 2025-12-08

Expose `get_tint_colour()` as a public function from `chives.media`.

## v17 - 2025-12-07

Account for [EXIF orientation](https://alexwlchan.net/til/2024/photos-can-have-orientation-in-exif/) when getting the width/height of image entities.

## v16 - 2025-12-06

Don't require defining `list_tags_in_metadata()` in projects that don't use tags.

## v15 - 2025-12-06

Fix a bunch of lints from ruff; remove an unused dependency.

## v14 - 2025-12-06

Improve the error message on failed assertions in `StaticSiteTestSuite`.

## v13 - 2025-12-06

Mark a couple more folders/files as ignored in `StaticSiteTestSuite`.

## v12 - 2025-12-06

Add checks for fuzzy tag matching to `StaticSiteTestSuite`.

## v11 - 2025-12-06

Add a new class `StaticSiteTestSuite` which runs my standard set of tests for a static site, e.g. checking every file is saved, checking timestamps use the correct format.

## v10 - 2025-12-05

Add a new `is_url_safe()` function for checking if a path can be safely used in a URL.

## v9 - 2025-12-05

This adds three models to `chives.media`: `ImageEntity`, `VideoEntity`, and `ImageEntity`.
These have all the information I need to show an image/video in a web page.

It also includes functions `create_image_entity` and `create_video_entity` which construct instances of these models.

## v8 - 2025-12-04

Add the `is_mastodon_host()` function.

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
