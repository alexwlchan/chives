"""
Tests for `chives.static_site_tests`.
"""

import os
from pathlib import Path
import shutil
import subprocess
from typing import Any, TypeVar

import pytest
from pytest import Pytester

from chives import dates


M = TypeVar("M")

GIT_ROOT = Path(
    subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
)


@pytest.fixture
def site_root(tmp_path: Path) -> Path:
    """
    Return a temp directory to use as a site root.
    """
    return tmp_path


def create_pyfile(
    pytester: Pytester,
    site_root: Path | None = None,
    metadata: Any = None,
    *,
    paths_in_metadata: set[Path] | None = None,
    tags_in_metadata: set[str] | None = None,
    date_formats: list[str] | None = None,
    known_similar_tags: set[tuple[str, str]] | None = None,
) -> None:
    """
    Create a new instance of `pytest.Pytester` which is ready to run
    a test suite based on StaticSiteTestSuite.
    """
    default_date_formats = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d",
    ]

    pytester.makepyfile(
        f"""
        from collections.abc import Iterator
        from pathlib import Path, PosixPath
        from typing import Any

        import pytest

        from chives.static_site_tests import (
            StaticSiteTestSuite,
            browser,
            pytest_generate_tests,
        )


        class TestSuite(StaticSiteTestSuite[Any]):
            @classmethod
            def get_site_root(self) -> Path:
                return Path({str(site_root or pytester.path)!r})

            @pytest.fixture
            def metadata(self, site_root: Path) -> Any:
                return {repr(metadata)}

            def list_paths_in_metadata(self, metadata: Any) -> set[Path]:
                return {repr(paths_in_metadata or set())}

            def list_tags_in_metadata(self, metadata: Any) -> Iterator[str]:
                yield from {repr(tags_in_metadata or set())}

            date_formats = {repr(date_formats or default_date_formats)}

            known_similar_tags = {repr(known_similar_tags or set())}
        """
    )


def test_paths_saved_locally_match_metadata(
    pytester: Pytester, site_root: Path
) -> None:
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

    create_pyfile(pytester, site_root, metadata, paths_in_metadata=set(metadata))

    keyword = (
        "test_every_file_in_metadata_is_saved_locally or "
        "test_every_local_file_is_in_metadata"
    )
    pytester.runpytest("-k", keyword).assert_outcomes(passed=2)

    # Add a new file locally, and check the test starts failing.
    (site_root / "media/fish.tiff").write_text("test")
    pytester.runpytest("-k", keyword).assert_outcomes(passed=1, failed=1)
    (site_root / "media/fish.tiff").unlink()

    # Delete one of the local files, and check the test starts failing.
    (site_root / "media/cat.jpg").unlink()
    pytester.runpytest("-k", keyword).assert_outcomes(passed=1, failed=1)


def test_checks_for_git_changes(pytester: Pytester, site_root: Path) -> None:
    """
    The tests check that there are no uncommitted Git changes.
    """
    create_pyfile(pytester, site_root)

    keyword = "test_no_uncommitted_git_changes"

    # Initially this should fail, because there isn't a Git repo in
    # the folder.
    pytester.runpytest("-k", keyword).assert_outcomes(failed=1)

    # Create a Git repo, add a file, and commit it.
    (site_root / "README.md").write_text("hello world")
    subprocess.check_call(["git", "init"], cwd=site_root)
    subprocess.check_call(["git", "add", "README.md"], cwd=site_root)
    subprocess.check_call(["git", "commit", "-m", "initial commit"], cwd=site_root)

    # Check there are no uncommitted Git changes
    pytester.runpytest("-k", keyword).assert_outcomes(passed=1)

    # Make a new change, and check it's spotted
    (site_root / "README.md").write_text("a different hello world")
    pytester.runpytest("-k", keyword).assert_outcomes(failed=1)


def test_checks_for_url_safe_paths(pytester: Pytester, site_root: Path) -> None:
    """
    The tests check for URL-safe paths.
    """
    create_pyfile(pytester, site_root)

    keyword = "test_every_path_is_url_safe"

    # This should pass trivially when the site is empty.
    pytester.runpytest("-k", keyword).assert_outcomes(passed=1)

    # Now write some files with URL-safe names, and check it's still okay.
    for filename in [
        "index.html",
        "metadata.js",
        ".DS_Store",
    ]:
        (site_root / filename).write_text("test")

    pytester.runpytest("-k", keyword).assert_outcomes(passed=1)

    # Write another file with a URL-unsafe name, and check it's caught
    # by the test.
    (site_root / "a#b#c").write_text("test")
    pytester.runpytest("-k", keyword).assert_outcomes(failed=1)


def test_checks_for_av1_videos(pytester: Pytester, site_root: Path) -> None:
    """
    The tests check for AV1-encoded videos.
    """
    create_pyfile(pytester, site_root)

    keyword = "test_no_videos_are_av1"

    # This should pass trivially when the site is empty.
    pytester.runpytest("-k", keyword).assert_outcomes(passed=1)

    # Copy in an H.264-encoded video, and check it's not flagged.
    shutil.copyfile(
        GIT_ROOT / "tests/fixtures/media/Sintel_360_10s_1MB_H264.mp4",
        site_root / "Sintel_360_10s_1MB_H264.mp4",
    )
    pytester.runpytest("-k", keyword).assert_outcomes(passed=1)

    # Copy in an AV1-encoded video, and check it's caught by the test
    shutil.copyfile(
        GIT_ROOT / "tests/fixtures/media/Sintel_360_10s_1MB_AV1.mp4",
        site_root / "Sintel_360_10s_1MB_AV1.mp4",
    )
    pytester.runpytest("-k", keyword).assert_outcomes(failed=1)


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
    def test_allows_correct_date_formats(
        self, pytester: Pytester, metadata: Any
    ) -> None:
        """
        The tests pass if all the dates are in the correct format.
        """
        create_pyfile(pytester, metadata=metadata)

        keyword = "test_all_timestamps_are_consistent"

        pytester.runpytest("-k", keyword).assert_outcomes(passed=1)

    @pytest.mark.parametrize("metadata", [{"date_saved": "AAAA-BB-CC"}])
    def test_rejects_incorrect_date_formats(
        self, pytester: Pytester, site_root: Path, metadata: Any
    ) -> None:
        """
        The tests fail if the metadata has inconsistent date formats.
        """
        create_pyfile(pytester, metadata=metadata)

        keyword = "test_all_timestamps_are_consistent"

        pytester.runpytest("-k", keyword).assert_outcomes(failed=1)

    def test_can_override_date_formats(self, pytester: Pytester) -> None:
        """
        A previously-blocked date format is allowed if you add it to
        the `date_formats` list.
        """
        metadata = {"date_saved": "2025"}
        keyword = "test_all_timestamps_are_consistent"

        # It fails with the default settings
        create_pyfile(pytester, metadata=metadata)
        pytester.runpytest("-k", keyword).assert_outcomes(failed=1)

        # It passes if we add the format to `date_formats`
        create_pyfile(pytester, metadata=metadata, date_formats=["%Y"])
        pytester.runpytest("-k", keyword).assert_outcomes(passed=1)


def test_checks_for_similar_tags(pytester: Pytester) -> None:
    """
    The tests check for similar and misspelt tags.
    """
    keyword = "test_no_similar_tags"

    # Check a site with distinct tags.
    create_pyfile(pytester, tags_in_metadata={"red", "green", "blue"})
    pytester.runpytest("-k", keyword).assert_outcomes(passed=1)

    # Check a site with similar tags.
    create_pyfile(pytester, tags_in_metadata={"red robot", "rod robot", "rid robot"})
    pytester.runpytest("-k", keyword).assert_outcomes(failed=1)

    # Check a site with similar tags, but marked as known-similar.
    create_pyfile(
        pytester,
        tags_in_metadata={"red robot", "rod robot", "green", "blue"},
        known_similar_tags={("red robot", "rod robot")},
    )
    pytester.runpytest("-k", keyword).assert_outcomes(passed=1)


@pytest.mark.skipif(
    "SKIP_PLAYWRIGHT" in os.environ, reason="skip slow Playwright tests"
)
class TestLoadsPageCorrectly:
    """
    Tests for `test_loads_page_correctly`.
    """

    def test_okay(self, pytester: Pytester, site_root: Path) -> None:
        """
        If the page contains valid HTML, the test passes.
        """
        keyword = "test_loads_page_correctly"

        subprocess.check_call(["playwright", "install", "webkit"], cwd=pytester.path)

        (site_root / "index.html").write_text("<p>Hello world!</p>")

        create_pyfile(pytester, site_root)
        pytester.runpytest("-k", keyword).assert_outcomes(passed=1)

    def test_noexist(self, pytester: Pytester) -> None:
        """
        If the page doesn't exist, the test fails.
        """
        keyword = "test_loads_page_correctly"

        subprocess.check_call(["playwright", "install", "webkit"], cwd=pytester.path)

        create_pyfile(pytester)
        pytester.runpytest("-k", keyword).assert_outcomes(failed=1)

    @pytest.mark.parametrize(
        "html",
        [
            # Invalid JavaScript
            "<script>???</script>",
            #
            # Valid JavaScript that logs an error.
            "<script>console.error('boom!')</script>",
        ],
    )
    def test_bad_js(self, pytester: Pytester, site_root: Path, html: str) -> None:
        """
        If the page loads but the JavaScript errors, the test fails.
        """
        keyword = "test_loads_page_correctly"

        subprocess.check_call(["playwright", "install", "webkit"], cwd=pytester.path)

        (site_root / "index.html").write_text(html)

        create_pyfile(pytester, site_root)
        pytester.runpytest("-k", keyword).assert_outcomes(failed=1)
