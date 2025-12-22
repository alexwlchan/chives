"""
Tests for `chives.static_site_tests`.
"""

from collections.abc import Iterator
from pathlib import Path
import shutil
import subprocess
from typing import Any, TypeVar

import pytest

from chives import dates
from chives.static_site_tests import StaticSiteTestSuite


M = TypeVar("M")


@pytest.fixture
def site_root(tmp_path: Path) -> Path:
    """
    Return a temp directory to use as a site root.
    """
    return tmp_path


def create_test_suite[M](
    site_root: Path,
    metadata: M,
    *,
    paths_in_metadata: set[Path] | None = None,
    tags_in_metadata: set[str] | None = None,
) -> StaticSiteTestSuite[M]:
    """
    Create a new instance of StaticSiteTestSuite with the hard-coded data
    provided.
    """

    class TestSuite(StaticSiteTestSuite[M]):
        def site_root(self) -> Path:  # pragma: no cover
            return site_root

        def metadata(self, site_root: Path) -> M:  # pragma: no cover
            return metadata

        def list_paths_in_metadata(self, metadata: M) -> set[Path]:
            return paths_in_metadata or set()

        def list_tags_in_metadata(self, metadata: M) -> Iterator[str]:
            yield from (tags_in_metadata or set())

    return TestSuite()


def test_paths_saved_locally_match_metadata(site_root: Path) -> None:
    """
    The tests check that the set of paths saved locally match the metadata.
    """
    # Create a series of paths in tmp_path.
    for filename in [
        "index.html",
        "metadata.js",
        "media/cat.jpg",
        "media/dog.png",
        "media/emu.gif",
        "viewer/index.html",
        ".DS_Store",
    ]:
        p = site_root / filename
        p.parent.mkdir(exist_ok=True)
        p.write_text("test")

    metadata = [Path("media/cat.jpg"), Path("media/dog.png"), Path("media/emu.gif")]

    t = create_test_suite(site_root, metadata, paths_in_metadata=set(metadata))
    t.test_every_file_in_metadata_is_saved_locally(metadata, site_root)
    t.test_every_local_file_is_in_metadata(metadata, site_root)

    # Add a new file locally, and check the test starts failing.
    (site_root / "media/fish.tiff").write_text("test")

    with pytest.raises(AssertionError):
        t.test_every_local_file_is_in_metadata(metadata, site_root)

    (site_root / "media/fish.tiff").unlink()

    # Delete one of the local files, and check the test starts failing.
    (site_root / "media/cat.jpg").unlink()

    with pytest.raises(AssertionError):
        t.test_every_file_in_metadata_is_saved_locally(metadata, site_root)


def test_checks_for_git_changes(site_root: Path) -> None:
    """
    The tests check that there are no uncommitted Git changes.
    """
    t = create_test_suite(site_root, metadata=[1, 2, 3])

    # Initially this should fail, because there isn't a Git repo in
    # the folder.
    with pytest.raises(AssertionError):
        t.test_no_uncommitted_git_changes(site_root)

    # Create a Git repo, add a file, and commit it.
    (site_root / "README.md").write_text("hello world")
    subprocess.check_call(["git", "init"], cwd=site_root)
    subprocess.check_call(["git", "add", "README.md"], cwd=site_root)
    subprocess.check_call(["git", "commit", "-m", "initial commit"], cwd=site_root)

    # Check there are no uncommitted Git changes
    t.test_no_uncommitted_git_changes(site_root)

    # Make a new change, and check it's spotted
    (site_root / "README.md").write_text("a different hello world")

    with pytest.raises(AssertionError):
        t.test_no_uncommitted_git_changes(site_root)


def test_checks_for_url_safe_paths(site_root: Path) -> None:
    """
    The tests check for URL-safe paths.
    """
    t = create_test_suite(site_root, metadata=[1, 2, 3])

    # This should pass trivially when the site is empty.
    t.test_every_path_is_url_safe(site_root)

    # Now write some files with URL-safe names, and check it's still okay.
    for filename in [
        "index.html",
        "metadata.js",
        ".DS_Store",
    ]:
        (site_root / filename).write_text("test")

    t.test_every_path_is_url_safe(site_root)

    # Write another file with a URL-unsafe name, and check it's caught
    # by the test.
    (site_root / "a#b#c").write_text("test")

    with pytest.raises(AssertionError):
        t.test_every_path_is_url_safe(site_root)


def test_checks_for_av1_videos(site_root: Path) -> None:
    """
    The tests check for AV1-encoded videos.
    """
    t = create_test_suite(site_root, metadata=[1, 2, 3])

    # This should pass trivially when the site is empty.
    t.test_no_videos_are_av1(site_root)

    # Copy in an H.264-encoded video, and check it's not flagged.
    shutil.copyfile(
        "tests/fixtures/media/Sintel_360_10s_1MB_H264.mp4",
        site_root / "Sintel_360_10s_1MB_H264.mp4",
    )
    t.test_no_videos_are_av1(site_root)

    # Copy in an AV1-encoded video, and check it's caught by the test
    shutil.copyfile(
        "tests/fixtures/media/Sintel_360_10s_1MB_AV1.mp4",
        site_root / "Sintel_360_10s_1MB_AV1.mp4",
    )
    with pytest.raises(AssertionError):
        t.test_no_videos_are_av1(site_root)


class TestAllTimestampsAreConsistent:
    """
    Tests for the `test_all_timestamps_are_consistent` method.
    """

    @pytest.mark.parametrize(
        "metadata",
        [
            {"date_saved": "2025-12-06"},
            {"date_saved": dates.now()},
        ],
    )
    def test_allows_correct_date_formats(self, site_root: Path, metadata: Any) -> None:
        """
        The tests pass if all the dates are in the correct format.
        """
        t = create_test_suite(site_root, metadata)
        t.test_all_timestamps_are_consistent(metadata)

    @pytest.mark.parametrize("metadata", [{"date_saved": "AAAA-BB-CC"}])
    def test_rejects_incorrect_date_formats(
        self, site_root: Path, metadata: Any
    ) -> None:
        """
        The tests fail if the metadata has inconsistent date formats.
        """
        t = create_test_suite(site_root, metadata)
        with pytest.raises(AssertionError):
            t.test_all_timestamps_are_consistent(metadata)

    def test_can_override_date_formats(self, site_root: Path) -> None:
        """
        A previously-blocked date format is allowed if you add it to
        the `date_formats` list.
        """
        metadata = {"date_saved": "2025"}
        t = create_test_suite(site_root, metadata)

        # It fails with the default settings
        with pytest.raises(AssertionError):
            t.test_all_timestamps_are_consistent(metadata)

        # It passes if we add the format to `date_formats`
        t.date_formats.append("%Y")
        t.test_all_timestamps_are_consistent(metadata)


def test_checks_for_similar_tags(site_root: Path) -> None:
    """
    The tests check for similar and misspelt tags.
    """
    metadata = [1, 2, 3]

    # Check a site with distinct tags.
    t1 = create_test_suite(
        site_root, metadata, tags_in_metadata={"red", "green", "blue"}
    )
    t1.test_no_similar_tags(metadata)

    # Check a site with similar tags.
    t2 = create_test_suite(
        site_root, metadata, tags_in_metadata={"red robot", "rod robot", "rid robot"}
    )
    with pytest.raises(AssertionError):
        t2.test_no_similar_tags(metadata)

    # Check a site with similar tags, but marked as known-similar.
    t3 = create_test_suite(
        site_root,
        metadata,
        tags_in_metadata={"red robot", "rod robot", "green", "blue"},
    )
    t3.known_similar_tags = {("red robot", "rod robot")}
    t3.test_no_similar_tags(metadata)
