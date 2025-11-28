"""Tests for `chives.media`."""

from chives import is_av1_video


def test_is_av1_video() -> None:
    """is_av1_video correctly detects AV1 videos."""
    # These two videos were downloaded from
    # https://test-videos.co.uk/sintel/mp4-h264 and
    # https://test-videos.co.uk/sintel/mp4-av1
    assert not is_av1_video("tests/fixtures/Sintel_360_10s_1MB_H264.mp4")
    assert is_av1_video("tests/fixtures/Sintel_360_10s_1MB_AV1.mp4")
