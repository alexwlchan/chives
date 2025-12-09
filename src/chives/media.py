"""
Functions for interacting with images/videos.

Dependencies:
* ffprobe
* https://github.com/alexwlchan/create_thumbnail
* https://github.com/alexwlchan/dominant_colours
* https://github.com/alexwlchan/get_live_text

References:
* https://alexwlchan.net/2021/dominant-colours/
* https://alexwlchan.net/2025/detecting-av1-videos/
* https://stackoverflow.com/a/58567453

"""

from fractions import Fraction
import json
from pathlib import Path
import subprocess
from typing import Literal, NotRequired, TypedDict, TYPE_CHECKING

if TYPE_CHECKING:
    import PIL


__all__ = [
    "create_image_entity",
    "create_video_entity",
    "get_media_paths",
    "get_tint_colour",
    "is_av1_video",
    "ImageEntity",
    "MediaEntity",
    "VideoEntity",
]


def is_av1_video(path: str | Path) -> bool:
    """
    Returns True if a video is encoded with AV1, False otherwise.
    """
    # fmt: off
    cmd = [
        "ffprobe",
        #
        # Set the logging level
        "-loglevel", "error",
        #
        # Select the first video stream
        "-select_streams", "v:0",
        #
        # Print the codec_name (e.g. av1)
        "-show_entries", "stream=codec_name",
        #
        # Print just the value
        "-output_format", "default=noprint_wrappers=1:nokey=1",
        #
        # Name of the video to check
        str(path),
    ]
    # fmt: on

    output = subprocess.check_output(cmd, text=True)

    return output.strip() == "av1"


class ImageEntity(TypedDict):
    """
    ImageEntity contains all the fields I need to render an image
    in a web page.
    """

    type: Literal["image"]

    # The path to the image on disk
    path: str

    # The path to a low-resolution thumbnail
    thumbnail_path: NotRequired[str]

    # The display resolution of the image
    width: int
    height: int

    # A hex-encoded colour which is prominent in this image.
    tint_colour: str

    # Whether the image is animated (GIF and WebP only)
    is_animated: NotRequired[Literal[True]]

    # Whether the image has transparent pixels
    has_transparency: NotRequired[Literal[True]]

    # The alt text of the image, if available
    alt_text: NotRequired[str]

    # The source URL of the image, if available
    source_url: NotRequired[str]


class VideoEntity(TypedDict):
    """
    VideoEntity contains all the fields I need to render a video
    in a web page.
    """

    type: Literal["video"]

    # The path to the video on disk
    path: str

    # The poster image for the video
    poster: ImageEntity

    # The display resolution of the video
    width: int
    height: int

    # The duration of the video, as an HOURS:MM:SS.MICROSECONDS string
    duration: str

    # Path to the subtitles for the video, if available
    subtitles_path: NotRequired[str]

    # The source URL of the image, if available
    source_url: NotRequired[str]

    # Whether the video should play automatically. This is used for
    # videos that are substituting for animated GIFs.
    autoplay: NotRequired[Literal[True]]


MediaEntity = ImageEntity | VideoEntity


def get_media_paths(e: MediaEntity) -> set[Path]:
    """
    Returns a list of all media paths represented by this media entity.
    """
    result: set[str | Path] = set()

    try:
        e["type"]
    except KeyError:
        raise TypeError(f"Entity does not have a type: {e}")

    if e["type"] == "video":
        result.add(e["path"])
        try:
            result.add(e["subtitles_path"])
        except KeyError:
            pass
        for p in get_media_paths(e["poster"]):
            result.add(p)
    elif e["type"] == "image":
        result.add(e["path"])
        try:
            result.add(e["thumbnail_path"])
        except KeyError:
            pass
    else:
        raise TypeError(f"Unrecognised entity type: {e['type']}")

    return {Path(p) for p in result}


class ThumbnailConfig(TypedDict):
    out_dir: Path | str
    width: NotRequired[int]
    height: NotRequired[int]


def create_image_entity(
    path: str | Path,
    *,
    background: str = "#ffffff",
    alt_text: str | None = None,
    source_url: str | None = None,
    thumbnail_config: ThumbnailConfig | None = None,
    generate_transcript: bool = False,
) -> ImageEntity:
    """
    Create an ImageEntity for a saved image.
    """
    from PIL import Image, ImageOps

    with Image.open(path) as im:
        # Account for EXIF orientation in the dimensions.
        # See https://alexwlchan.net/til/2024/photos-can-have-orientation-in-exif/
        transposed_im = ImageOps.exif_transpose(im)

        entity: ImageEntity = {
            "type": "image",
            "path": str(path),
            "tint_colour": get_tint_colour(path, background=background),
            "width": transposed_im.width,
            "height": transposed_im.height,
        }

        if _is_animated(im):
            entity["is_animated"] = True

        if _has_transparency(im):
            entity["has_transparency"] = True

    if thumbnail_config is not None:
        entity["thumbnail_path"] = _create_thumbnail(path, thumbnail_config)

    if alt_text is not None and generate_transcript:
        raise TypeError("You cannot set alt_text and generate_transcript=True!")

    elif alt_text is not None:
        entity["alt_text"] = alt_text
    elif generate_transcript:
        transcript = _get_transcript(path)
        if transcript is not None:
            entity["alt_text"] = transcript

    if source_url is not None:
        entity["source_url"] = source_url

    return entity


def create_video_entity(
    video_path: str | Path,
    *,
    poster_path: str | Path,
    subtitles_path: str | Path | None = None,
    source_url: str | None = None,
    autoplay: bool = False,
    thumbnail_config: ThumbnailConfig | None = None,
    background: str = "#ffffff",
) -> VideoEntity:
    """
    Create a video entity for files on disk.
    """
    width, height, duration = _get_video_data(video_path)
    poster = create_image_entity(
        poster_path, thumbnail_config=thumbnail_config, background=background
    )

    entity: VideoEntity = {
        "type": "video",
        "path": str(video_path),
        "width": width,
        "height": height,
        "duration": duration,
        "poster": poster,
    }

    if subtitles_path:
        entity["subtitles_path"] = str(subtitles_path)

    if source_url:
        entity["source_url"] = source_url

    if autoplay:
        entity["autoplay"] = autoplay

    return entity


def _is_animated(im: "PIL.Image.Image") -> bool:
    """
    Returns True if an image is animated, False otherwise.
    """
    return getattr(im, "is_animated", False)


def _has_transparency(im: "PIL.Image.Image") -> bool:
    """
    Returns True if an image has transparent pixels, False otherwise.

    By Vinyl Da.i'gyu-Kazotetsu on Stack Overflow:
    https://stackoverflow.com/a/58567453
    """
    if im.info.get("transparency", None) is not None:
        return True
    if im.mode == "P":
        transparent = im.info.get("transparency", -1)
        for _, index in im.getcolors():  # type: ignore
            # TODO: Find an image that hits this branch, so I can
            # include it in the test suite.
            if index == transparent:  # pragma: no cover
                return True
    elif im.mode == "RGBA":
        extrema = im.getextrema()
        if extrema[3][0] < 255:  # type: ignore
            return True
    return False


def get_tint_colour(path: str | Path, *, background: str) -> str:
    """
    Get the tint colour for an image.
    """
    if background == "white":
        background = "#ffffff"
    elif background == "black":
        background = "#000000"

    result = subprocess.check_output(
        ["dominant_colours", str(path), "--best-against-bg", background], text=True
    )
    return result.strip()


def _get_transcript(path: str | Path) -> str | None:
    """
    Get the transcript for an image (if any).
    """
    result = subprocess.check_output(["get_live_text", str(path)], text=True)

    return result.strip() or None


def _create_thumbnail(path: str | Path, thumbnail_config: ThumbnailConfig) -> str:
    """
    Create a thumbnail for an image and return the path.
    """
    cmd = ["create_thumbnail", str(path), "--out-dir", thumbnail_config["out_dir"]]

    if "width" in thumbnail_config:
        cmd.extend(["--width", str(thumbnail_config["width"])])

    if "height" in thumbnail_config:
        cmd.extend(["--height", str(thumbnail_config["height"])])

    return subprocess.check_output(cmd, text=True)


def _get_video_data(video_path: str | Path) -> tuple[int, int, str]:
    """
    Returns the dimensions and duration of a video, as a width/height fraction.
    """
    cmd = [
        "ffprobe",
        #
        # verbosity level = error
        "-v",
        "error",
        #
        # only get information about the first video stream
        "-select_streams",
        "v:0",
        #
        # only gather the entries I'm interested in
        "-show_entries",
        "stream=width,height,sample_aspect_ratio,duration",
        #
        # print the duration in HH:MM:SS.microseconds format
        "-sexagesimal",
        #
        # print output in JSON, which is easier to parse
        "-print_format",
        "json",
        #
        # input file
        str(video_path),
    ]

    output = subprocess.check_output(cmd)
    ffprobe_resp = json.loads(output)

    # The output will be structured something like:
    #
    #   {
    #       "streams": [
    #           {
    #               "width": 1920,
    #               "height": 1080,
    #               "sample_aspect_ratio": "45:64"
    #           }
    #       ],
    #       …
    #   }
    #
    # If the video doesn't specify a pixel aspect ratio, then it won't
    # have a `sample_aspect_ratio` key.
    video_stream = ffprobe_resp["streams"][0]

    try:
        pixel_aspect_ratio = Fraction(
            video_stream["sample_aspect_ratio"].replace(":", "/")
        )
    except KeyError:
        pixel_aspect_ratio = Fraction(1)

    width = round(video_stream["width"] * pixel_aspect_ratio)
    height = video_stream["height"]
    duration = video_stream["duration"]

    return width, height, duration
