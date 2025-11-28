"""
Functions for interacting with images/videos.

References:
* https://alexwlchan.net/2025/detecting-av1-videos/

"""

from pathlib import Path

from pymediainfo import MediaInfo


def is_av1_video(path: str | Path) -> bool:
    """
    Returns True if a video is encoded with AV1, False otherwise.
    """
    media_info = MediaInfo.parse(path)
    video_codec: str = media_info.video_tracks[0].codec_id

    return video_codec == "av01"
