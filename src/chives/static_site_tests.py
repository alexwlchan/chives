"""
Defines a set of common tests and test helpers used for all my static sites.
"""

from abc import ABC, abstractmethod
import collections
from collections.abc import Iterator
import glob
import itertools
import os
from pathlib import Path
import subprocess
from typing import cast, TypedDict, TypeVar

from javascript_data_files import read_typed_js
import pytest
from rapidfuzz import fuzz

from chives.dates import date_matches_any_format, find_all_dates
from chives.media import is_av1_video
from chives.urls import is_url_safe


T = TypeVar("T")


class StaticSiteTestSuite[M](ABC):
    """
    Defines a base set of tests to run against any of my static sites.

    This should be subclassed as a Test* class, which allows you to use
    the fixtures and write site-specific tests.
    """

    @abstractmethod
    @pytest.fixture
    def site_root(self) -> Path:
        """
        Returns the path to the folder at the root of the site.
        """
        ...

    @abstractmethod
    @pytest.fixture
    def metadata(self, site_root: Path) -> M:
        """
        Returns all the metadata for this project.
        """
        ...

    @abstractmethod
    def list_paths_in_metadata(self, metadata: M) -> set[Path]:
        """
        Returns a set of paths described in the metadata.
        """
        ...

    @abstractmethod
    def list_tags_in_metadata(self, metadata: M) -> Iterator[str]:
        """
        Returns all the tags used in the metadata, once for every usage.

        For example, if three documents use the same tag, the tag will
        be returned three times.
        """
        ...

    def test_no_uncommitted_git_changes(self, site_root: Path) -> None:
        """
        There are no changes which haven't been committed to Git.

        This is especially useful when I run a script that tests all
        my static sites, that none of them have unsaved changes.
        """
        rc = subprocess.call(["git", "diff", "--exit-code", "--quiet"], cwd=site_root)

        assert rc == 0, "There are uncommitted changes!"

    def list_paths_saved_locally(self, site_root: Path) -> set[Path]:
        """
        Returns a set of paths saved locally.
        """
        paths_saved_locally = set()

        for root, _, filenames in site_root.walk():
            # Ignore certain top-level folders I don't care about.
            try:
                top_level_folder = root.relative_to(site_root).parts[0]
            except IndexError:
                pass
            else:
                if top_level_folder in {
                    ".git",
                    ".mypy_cache",
                    ".pytest_cache",
                    ".ruff_cache",
                    ".venv",
                    "data",
                    "scripts",
                    "static",
                    "tests",
                    "viewer",
                }:
                    continue

            for f in filenames:
                if f == ".DS_Store":
                    continue

                if root == site_root and f in {
                    "Icon\r",
                    ".gitignore",
                    "index.html",
                    "README.md",
                    "TODO.md",
                }:
                    continue

                if root == site_root and f.endswith(".js"):
                    continue

                paths_saved_locally.add((root / f).relative_to(site_root))

        return paths_saved_locally

    def test_every_file_in_metadata_is_saved_locally(
        self, metadata: M, site_root: Path
    ) -> None:
        """
        Every file described in the metadata is saved locally.
        """
        paths_in_metadata = self.list_paths_in_metadata(metadata)
        paths_saved_locally = self.list_paths_saved_locally(site_root)

        assert paths_in_metadata - paths_saved_locally == set(), (
            f"Paths in metadata not saved locally: {paths_in_metadata - paths_saved_locally}"
        )

    def test_every_local_file_is_in_metadata(
        self, metadata: M, site_root: Path
    ) -> None:
        """
        Every file saved locally is described in the metadata.
        """
        paths_in_metadata = self.list_paths_in_metadata(metadata)
        paths_saved_locally = self.list_paths_saved_locally(site_root)

        assert paths_saved_locally - paths_in_metadata == set()

    def test_every_path_is_url_safe(self, site_root: Path) -> None:
        """
        Every path has a URL-safe path.
        """
        bad_paths = set()

        for root, _, filenames in site_root.walk():
            for f in filenames:
                p = site_root / root / f
                if not is_url_safe(p):
                    bad_paths.add(p)

        assert bad_paths == set()

    @pytest.mark.skipif("SKIP_AV1" in os.environ, reason="skip slow test")
    def test_no_videos_are_av1(self, site_root: Path) -> None:
        """
        No videos are encoded in AV1 (which doesn't play on my iPhone).

        This test can be removed when I upgrade all my devices to ones with
        hardware AV1 decoding support.

        See https://alexwlchan.net/2025/av1-on-my-iphone/
        """
        av1_videos = set()

        av1_videos = {
            p
            for p in glob.glob("**/*.mp4", root_dir=site_root, recursive=True)
            if is_av1_video(site_root / p)
        }

        assert av1_videos == set()

    date_formats = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d",
    ]

    def test_all_timestamps_are_consistent(self, metadata: M) -> None:
        """
        All the timestamps in my JSON use a consistent format.

        See https://alexwlchan.net/2025/messy-dates-in-json/
        """
        bad_date_strings = {
            date_string
            for _, _, date_string in find_all_dates(metadata)
            if not date_matches_any_format(date_string, self.date_formats)
        }

        assert bad_date_strings == set()

    @staticmethod
    def find_similar_pairs(tags: dict[str, int]) -> Iterator[tuple[str, str]]:
        """
        Find pairs of similar-looking tags in the collection `tags`.
        """
        for t1, t2 in itertools.combinations(sorted(tags), 2):
            if fuzz.ratio(t1, t2) > 80:
                yield (t1, t2)

    known_similar_tags: set[tuple[str, str]] = set()

    def test_no_similar_tags(self, metadata: M) -> None:
        """
        There are no similar/misspelt tags.
        """
        tags = collections.Counter(self.list_tags_in_metadata(metadata))

        bad_tags = [
            f"{t1} ({tags[t1]}) / {t2} ({tags[t2]})"
            for t1, t2 in self.find_similar_pairs(tags)
            if (t1, t2) not in self.known_similar_tags
        ]

        assert bad_tags == []
