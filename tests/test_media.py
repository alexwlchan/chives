"""Tests for `chives.media`."""

from pathlib import Path
from typing import Any

from PIL import Image
import pytest

from chives.media import (
    create_image_entity,
    create_video_entity,
    get_media_paths,
    is_av1_video,
)


@pytest.fixture
def fixtures_dir() -> Path:
    """
    Returns the directory where media fixtures are stored.
    """
    return Path("tests/fixtures/media")


def test_is_av1_video(fixtures_dir: Path) -> None:
    """is_av1_video correctly detects AV1 videos."""
    # These two videos were downloaded from
    # https://test-videos.co.uk/sintel/mp4-h264 and
    # https://test-videos.co.uk/sintel/mp4-av1
    assert not is_av1_video(fixtures_dir / "Sintel_360_10s_1MB_H264.mp4")
    assert is_av1_video(fixtures_dir / "Sintel_360_10s_1MB_AV1.mp4")


class TestCreateImageEntity:
    """
    Tests for create_image_entity().
    """

    def test_basic_image(self, fixtures_dir: Path) -> None:
        """
        Get an image entity for a basic blue square.
        """
        entity = create_image_entity(fixtures_dir / "blue.png")
        assert entity == {
            "type": "image",
            "path": "tests/fixtures/media/blue.png",
            "width": 32,
            "height": 16,
            "tint_colour": "#0000ff",
        }

    @pytest.mark.parametrize(
        "filename",
        [
            # This is a solid blue image with a section in the middle deleted
            "blue_with_hole.png",
            #
            # An asteroid belt drawn in TikZ by TeX.SE user Qrrbrbirlbel,
            # which has `transparency` in its im.info.
            # Downloaded from http://tex.stackexchange.com/a/111974/9668
            "asteroid_belt.png",
        ],
    )
    def test_image_with_transparency(self, fixtures_dir: Path, filename: str) -> None:
        """
        If an image has transparent pixels, then the entity has
        `has_transparency=True`.
        """
        entity = create_image_entity(fixtures_dir / filename)
        assert entity["has_transparency"]

    @pytest.mark.parametrize(
        "filename",
        [
            "blue.png",
            "space.jpg",
            #
            # An animated electric field drawn in TikZ.
            # Downloaded from https://tex.stackexchange.com/a/158930/9668
            "electric_field.gif",
        ],
    )
    def test_image_without_transparency(
        self, fixtures_dir: Path, filename: str
    ) -> None:
        """
        If an image has no transparent pixels, then the entity doesn't
        have a `has_transparency` key.
        """
        entity = create_image_entity(fixtures_dir / filename)
        assert "has_transparency" not in entity

    # These test files were downloaded from Dave Perrett repo:
    # https://github.com/recurser/exif-orientation-examples

    @pytest.mark.parametrize(
        "filename",
        [
            "Landscape_0.jpg",
            "Landscape_1.jpg",
            "Landscape_2.jpg",
            "Landscape_3.jpg",
            "Landscape_4.jpg",
            "Landscape_5.jpg",
            "Landscape_6.jpg",
            "Landscape_7.jpg",
            "Landscape_8.jpg",
        ],
    )
    def test_accounts_for_exif_orientation(
        self, fixtures_dir: Path, filename: str
    ) -> None:
        """
        The dimensions are the display dimensions, which accounts for
        the EXIF orientation.
        """
        entity = create_image_entity(fixtures_dir / filename)
        assert (entity["width"], entity["height"]) == (1800, 1200)

    def test_animated_image(self, fixtures_dir: Path) -> None:
        """
        If an image is animated, the entity has `is_animated=True`.
        """
        # An animated electric field drawn in TikZ.
        # Downloaded from https://tex.stackexchange.com/a/158930/9668
        entity = create_image_entity(fixtures_dir / "electric_field.gif")
        assert entity["is_animated"]

    def test_other_attrs_are_forwarded(self, fixtures_dir: Path) -> None:
        """
        The `alt_text` and `source_url` values are forwarded to the
        final entity.
        """
        entity = create_image_entity(
            fixtures_dir / "blue.png",
            alt_text="This is the alt text",
            source_url="https://example.com/blue.png",
        )

        assert entity["alt_text"] == "This is the alt text"
        assert entity["source_url"] == "https://example.com/blue.png"

    def test_alt_text_and_generate_transcript_is_error(
        self, fixtures_dir: Path
    ) -> None:
        """
        You can't pass `alt_text` and `generate_transcript` at the same time.
        """
        with pytest.raises(TypeError):
            create_image_entity(
                fixtures_dir / "blue.png",
                alt_text="This is the alt text",
                generate_transcript=True,
            )

    def test_generate_transcript(self, fixtures_dir: Path) -> None:
        """
        If you pass `generate_transcript=True`, the image is OCR'd for alt text.
        """
        entity = create_image_entity(
            fixtures_dir / "underlined_text.png", generate_transcript=True
        )
        assert entity["alt_text"] == "I visited Berlin in Germany."

    def test_generate_transcript_if_no_text(self, fixtures_dir: Path) -> None:
        """
        If you pass `generate_transcript=True` for an image with no text,
        you don't get any alt text.
        """
        entity = create_image_entity(
            fixtures_dir / "blue.png", generate_transcript=True
        )
        assert "alt_text" not in entity

    def test_create_thumbnail_by_width(
        self, fixtures_dir: Path, tmp_path: Path
    ) -> None:
        """
        Create a thumbnail by width.
        """
        entity = create_image_entity(
            fixtures_dir / "blue.png",
            thumbnail_config={"out_dir": tmp_path / "thumbnails", "width": 10},
        )

        assert Path(entity["thumbnail_path"]).exists()

        with Image.open(entity["thumbnail_path"]) as im:
            assert im.width == 10

    def test_create_thumbnail_by_height(
        self, fixtures_dir: Path, tmp_path: Path
    ) -> None:
        """
        Create a thumbnail by height.
        """
        entity = create_image_entity(
            fixtures_dir / "blue.png",
            thumbnail_config={"out_dir": tmp_path / "thumbnails", "height": 5},
        )

        assert Path(entity["thumbnail_path"]).exists()

        with Image.open(entity["thumbnail_path"]) as im:
            assert im.height == 5

    @pytest.mark.parametrize(
        "background, tint_colour",
        [
            ("white", "#005493"),
            ("black", "#b3fdff"),
            ("#111111", "#b3fdff"),
        ],
    )
    def test_tint_colour_is_based_on_background(
        self, fixtures_dir: Path, background: str, tint_colour: str
    ) -> None:
        """
        The tint colour is based to suit the background.
        """
        # This is a checkerboard pattern made of 2 different shades of
        # turquoise, a light and a dark.
        entity = create_image_entity(
            fixtures_dir / "checkerboard.png", background=background
        )
        assert entity["tint_colour"] == tint_colour


class TestCreateVideoEntity:
    """
    Tests for `create_video_entity()`.
    """

    def test_basic_video(self, fixtures_dir: Path) -> None:
        """
        Get a video entity for a basic video.
        """
        # This video was downloaded from
        # https://test-videos.co.uk/sintel/mp4-h264
        entity = create_video_entity(
            fixtures_dir / "Sintel_360_10s_1MB_H264.mp4",
            poster_path=fixtures_dir / "Sintel_360_10s_1MB_H264.png",
        )
        assert entity == {
            "type": "video",
            "path": "tests/fixtures/media/Sintel_360_10s_1MB_H264.mp4",
            "width": 640,
            "height": 360,
            "duration": "0:00:10.000000",
            "poster": {
                "type": "image",
                "path": "tests/fixtures/media/Sintel_360_10s_1MB_H264.png",
                "tint_colour": "#020202",
                "width": 640,
                "height": 360,
            },
        }

    def test_other_attrs_are_forwarded(self, fixtures_dir: Path) -> None:
        """
        The `subtitles_path`, `source_url` and `autoplay` values are
        forwarded to the final entity.
        """
        entity = create_video_entity(
            fixtures_dir / "Sintel_360_10s_1MB_H264.mp4",
            poster_path=fixtures_dir / "Sintel_360_10s_1MB_H264.png",
            subtitles_path=fixtures_dir / "Sintel_360_10s_1MB_H264.en.vtt",
            source_url="https://test-videos.co.uk/sintel/mp4-h264",
            autoplay=True,
        )

        assert (
            entity["subtitles_path"]
            == "tests/fixtures/media/Sintel_360_10s_1MB_H264.en.vtt"
        )
        assert entity["source_url"] == "https://test-videos.co.uk/sintel/mp4-h264"
        assert entity["autoplay"]

    def test_gets_display_dimensions(self, fixtures_dir: Path) -> None:
        """
        The width/height dimensions are based on the display aspect ratio,
        not the storage aspect ratio.

        See https://alexwlchan.net/2025/square-pixels/
        """
        # This is a short clip of https://www.youtube.com/watch?v=HHhyznZ2u4E
        entity = create_video_entity(
            fixtures_dir / "Mars 2020 EDL Remastered [HHhyznZ2u4E].mp4",
            poster_path=fixtures_dir / "Mars 2020 EDL Remastered [HHhyznZ2u4E].jpg",
        )

        assert entity["width"] == 1350
        assert entity["height"] == 1080

    def test_video_without_sample_aspect_ratio(self, fixtures_dir: Path) -> None:
        """
        Get the width/height dimensions of a video that doesn't have
        `sample_aspect_ratio` in its metadata.
        """
        # This is a short clip from Wings (1927).
        entity = create_video_entity(
            fixtures_dir / "wings_tracking_shot.mp4",
            poster_path=fixtures_dir / "wings_tracking_shot.jpg",
        )

        assert entity["width"] == 960
        assert entity["height"] == 720

    @pytest.mark.parametrize(
        "background, tint_colour",
        [
            ("white", "#005493"),
            ("black", "#b3fdff"),
            ("#111111", "#b3fdff"),
        ],
    )
    def test_tint_colour_is_based_on_background(
        self, fixtures_dir: Path, background: str, tint_colour: str
    ) -> None:
        """
        The tint colour is based to suit the background.
        """
        # The poster image is a checkerboard pattern made of 2 different
        # shades of turquoise, a light and a dark.
        entity = create_video_entity(
            fixtures_dir / "Sintel_360_10s_1MB_H264.mp4",
            poster_path=fixtures_dir / "checkerboard.png",
            background=background,
        )
        assert entity["poster"]["tint_colour"] == tint_colour

    def test_video_with_thumbnail(self, fixtures_dir: Path, tmp_path: Path) -> None:
        """
        Create a low-resolution thumbnail of the poster image.
        """
        entity = create_video_entity(
            fixtures_dir / "Sintel_360_10s_1MB_H264.mp4",
            poster_path=fixtures_dir / "Sintel_360_10s_1MB_H264.png",
            thumbnail_config={"out_dir": tmp_path / "thumbnails", "width": 300},
        )

        assert entity["poster"]["thumbnail_path"] == str(
            tmp_path / "thumbnails/Sintel_360_10s_1MB_H264.png"
        )
        assert Path(entity["poster"]["thumbnail_path"]).exists()


class TestGetMediaPaths:
    """
    Tests for `get_media_paths`.
    """

    def test_basic_image(self, fixtures_dir: Path) -> None:
        """
        An image with no thumbnail only has one path: the image.
        """
        entity = create_image_entity(fixtures_dir / "blue.png")
        assert get_media_paths(entity) == {fixtures_dir / "blue.png"}

    def test_image_with_thumbnail(self, fixtures_dir: Path, tmp_path: Path) -> None:
        """
        An image with a thumbnail has two paths: the video and the
        thumbnail.
        """
        entity = create_image_entity(
            fixtures_dir / "blue.png",
            thumbnail_config={"out_dir": tmp_path / "thumbnails", "width": 300},
        )
        assert get_media_paths(entity) == {
            fixtures_dir / "blue.png",
            tmp_path / "thumbnails/blue.png",
        }

    def test_video(self, fixtures_dir: Path) -> None:
        """
        A video has two paths: the video and the poster image.
        """
        entity = create_video_entity(
            fixtures_dir / "Sintel_360_10s_1MB_H264.mp4",
            poster_path=fixtures_dir / "Sintel_360_10s_1MB_H264.png",
        )
        assert get_media_paths(entity) == {
            fixtures_dir / "Sintel_360_10s_1MB_H264.mp4",
            fixtures_dir / "Sintel_360_10s_1MB_H264.png",
        }

    def test_video_with_subtitles(self, fixtures_dir: Path) -> None:
        """
        A video with subtitles has three paths: the video, the subtitles,
        and the poster image.
        """
        entity = create_video_entity(
            fixtures_dir / "Sintel_360_10s_1MB_H264.mp4",
            poster_path=fixtures_dir / "Sintel_360_10s_1MB_H264.png",
            subtitles_path=fixtures_dir / "Sintel_360_10s_1MB_H264.en.vtt",
        )
        assert get_media_paths(entity) == {
            fixtures_dir / "Sintel_360_10s_1MB_H264.mp4",
            fixtures_dir / "Sintel_360_10s_1MB_H264.png",
            fixtures_dir / "Sintel_360_10s_1MB_H264.en.vtt",
        }

    def test_video_with_thumbnail(self, fixtures_dir: Path, tmp_path: Path) -> None:
        """
        A video with a poster thumbnail has three paths: the video,
        the poster image, and the poster thumbnail.
        """
        entity = create_video_entity(
            fixtures_dir / "Sintel_360_10s_1MB_H264.mp4",
            poster_path=fixtures_dir / "Sintel_360_10s_1MB_H264.png",
            thumbnail_config={"out_dir": tmp_path / "thumbnails", "width": 300},
        )
        assert get_media_paths(entity) == {
            fixtures_dir / "Sintel_360_10s_1MB_H264.mp4",
            fixtures_dir / "Sintel_360_10s_1MB_H264.png",
            tmp_path / "thumbnails/Sintel_360_10s_1MB_H264.png",
        }

    @pytest.mark.parametrize("bad_entity", [{}, {"type": "shape"}])
    def test_unrecognised_entity_is_error(self, bad_entity: Any) -> None:
        """
        Getting media paths for an unrecognised entity type is a TypeError.
        """
        with pytest.raises(TypeError):
            get_media_paths(bad_entity)
