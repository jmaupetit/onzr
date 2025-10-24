"""Onzr deezer tests."""

import pytest
from pydantic import HttpUrl

from onzr.deezer import StreamQuality, Track, TrackStatus
from onzr.exceptions import DeezerTrackException
from onzr.models import TrackInfo, TrackShort
from tests.factories import DeezerSongFactory, DeezerSongResponseFactory


def test_stream_quality_enum():
    """Test the StreamQuality enum."""
    assert StreamQuality.FLAC.media_type == "audio/flac"
    assert StreamQuality.MP3_320.media_type == "audio/mpeg"
    assert StreamQuality.MP3_128.media_type == "audio/mpeg"


def test_track_init(configured_onzr, responses):
    """Test the Track instantiation."""
    track_id = 1
    track_token = "fake"  # noqa: S105
    track_duration = 120
    track_artist = "Jimi Hendrix"
    track_title = "All along the watchtower"
    track_version = "(Dylan remix)"
    track_album = "Experience"
    track_picture = "ABCDEF"
    track_filesize_mp3_128 = 128
    track_filesize_mp3_320 = 320
    track_filesize_flac = 7142

    responses.post(
        "http://www.deezer.com/ajax/gw-light.php",
        status=200,
        json=DeezerSongResponseFactory.build(
            error={},
            results=DeezerSongFactory.build(
                SNG_ID=track_id,
                TRACK_TOKEN=track_token,
                DURATION=track_duration,
                ART_NAME=track_artist,
                SNG_TITLE=track_title,
                VERSION=track_version,
                ALB_TITLE=track_album,
                ALB_PICTURE=track_picture,
                FILESIZE_MP3_128=track_filesize_mp3_128,
                FILESIZE_MP3_320=track_filesize_mp3_320,
                FILESIZE_FLAC=track_filesize_flac,
            ),
        ).model_dump(),
    )

    track = Track(client=configured_onzr.deezer, track_id=track_id, background=False)

    assert track.track_id == track_id
    assert track.key == b"4den4:}:g,#j3i`a"
    assert track.status == TrackStatus.IDLE
    assert track.streamed == 0
    assert track.track_info == TrackInfo(
        id=track_id,
        token=track_token,
        duration=track_duration,
        artist=track_artist,
        title=f"{track_title} {track_version}",
        album=track_album,
        picture=track_picture,
        formats=[
            StreamQuality.MP3_128,
            StreamQuality.MP3_320,
            StreamQuality.FLAC,
        ],
    )
    assert track.token == track_token
    assert track.duration == track_duration
    assert track.artist == track_artist
    assert track.title == f"{track_title} {track_version}"
    assert track.album == track_album
    assert track.picture == track_picture
    assert track.cover_small == HttpUrl(
        "https://e-cdns-images.dzcdn.net/images/cover/ABCDEF/56x56-000000-80-0-0.jpg"
    )
    assert track.cover_medium == HttpUrl(
        "https://e-cdns-images.dzcdn.net/images/cover/ABCDEF/250x250-000000-80-0-0.jpg"
    )
    assert track.cover_big == HttpUrl(
        "https://e-cdns-images.dzcdn.net/images/cover/ABCDEF/500x500-000000-80-0-0.jpg"
    )
    assert track.cover_xl == HttpUrl(
        "https://e-cdns-images.dzcdn.net/images/cover/ABCDEF/1000x1000-000000-80-0-0.jpg"
    )
    assert (
        track.full_title
        == f"{track_artist} - {track_title} {track_version} [{track_album}]"
    )

    # If picture is None
    track.track_info.picture = None
    assert track.cover_small is None
    assert track.cover_medium is None
    assert track.cover_big is None
    assert track.cover_xl is None
    assert track.formats == [
        StreamQuality.MP3_128,
        StreamQuality.MP3_320,
        StreamQuality.FLAC,
    ]

    # Test available formats
    responses.post(
        "http://www.deezer.com/ajax/gw-light.php",
        status=200,
        json=DeezerSongResponseFactory.build(
            error={},
            results=DeezerSongFactory.build(
                SNG_ID=track_id,
                TRACK_TOKEN=track_token,
                DURATION=track_duration,
                ART_NAME=track_artist,
                SNG_TITLE=track_title,
                ALB_TITLE=track_album,
                ALB_PICTURE=track_picture,
                FILESIZE_MP3_128=track_filesize_mp3_128,
                FILESIZE_MP3_320=track_filesize_mp3_320,
                FILESIZE_FLAC=0,
            ),
        ).model_dump(),
    )
    track = Track(client=configured_onzr.deezer, track_id=track_id, background=False)

    assert track.formats == [
        StreamQuality.MP3_128,
        StreamQuality.MP3_320,
    ]

    # Test when none of configured formats are available
    responses.post(
        "http://www.deezer.com/ajax/gw-light.php",
        status=200,
        json=DeezerSongResponseFactory.build(
            error={},
            results=DeezerSongFactory.build(
                SNG_ID=track_id,
                TRACK_TOKEN=track_token,
                DURATION=track_duration,
                ART_NAME=track_artist,
                SNG_TITLE=track_title,
                VERSION="",
                ALB_TITLE=track_album,
                ALB_PICTURE=track_picture,
                FILESIZE_MP3_128=0,
                FILESIZE_MP3_320=0,
                FILESIZE_FLAC=0,
            ),
        ).model_dump(),
    )
    with pytest.raises(
        DeezerTrackException,
        match=r"No available formats detected for track \d+$",
    ):
        Track(client=configured_onzr.deezer, track_id=track_id, background=False)

    # Test when no version is supplied (empty string)
    responses.post(
        "http://www.deezer.com/ajax/gw-light.php",
        status=200,
        json=DeezerSongResponseFactory.build(
            error={},
            results=DeezerSongFactory.build(
                SNG_ID=track_id,
                TRACK_TOKEN=track_token,
                DURATION=track_duration,
                ART_NAME=track_artist,
                SNG_TITLE=track_title,
                VERSION="",
                ALB_TITLE=track_album,
                ALB_PICTURE=track_picture,
                FILESIZE_MP3_128=track_filesize_mp3_128,
                FILESIZE_MP3_320=track_filesize_mp3_320,
                FILESIZE_FLAC=track_filesize_flac,
            ),
        ).model_dump(),
    )

    track = Track(client=configured_onzr.deezer, track_id=track_id, background=False)
    assert track.title == track_title

    # Test when no version is supplied (field not in payload)
    payload = DeezerSongResponseFactory.build(
        error={},
        results=DeezerSongFactory.build(
            SNG_ID=track_id,
            TRACK_TOKEN=track_token,
            DURATION=track_duration,
            ART_NAME=track_artist,
            SNG_TITLE=track_title,
            ALB_TITLE=track_album,
            ALB_PICTURE=track_picture,
            FILESIZE_MP3_128=track_filesize_mp3_128,
            FILESIZE_MP3_320=track_filesize_mp3_320,
            FILESIZE_FLAC=track_filesize_flac,
        ),
    )
    del payload.results.VERSION

    responses.post(
        "http://www.deezer.com/ajax/gw-light.php",
        status=200,
        json=payload.model_dump(),
    )

    track = Track(client=configured_onzr.deezer, track_id=track_id, background=False)
    assert track.title == track_title


def test_track_query_quality(configured_onzr, responses):
    """Test the track query_quality method."""
    track_id = 1
    track_token = "fake"  # noqa: S105
    track_duration = 120
    track_artist = "Jimi Hendrix"
    track_title = "All along the watchtower"
    track_album = "Experience"
    track_picture = "ABCDEF"
    track_filesize_mp3_128 = 128
    track_filesize_mp3_320 = 320

    responses.post(
        "http://www.deezer.com/ajax/gw-light.php",
        status=200,
        json=DeezerSongResponseFactory.build(
            error={},
            results=DeezerSongFactory.build(
                SNG_ID=track_id,
                TRACK_TOKEN=track_token,
                DURATION=track_duration,
                ART_NAME=track_artist,
                SNG_TITLE=track_title,
                ALB_TITLE=track_album,
                ALB_PICTURE=track_picture,
                FILESIZE_MP3_128=track_filesize_mp3_128,
                FILESIZE_MP3_320=track_filesize_mp3_320,
                FILESIZE_FLAC=0,
            ),
        ).model_dump(),
    )
    track = Track(client=configured_onzr.deezer, track_id=track_id, background=False)

    assert track.query_quality(StreamQuality.MP3_128) == StreamQuality.MP3_128
    assert track.query_quality(StreamQuality.MP3_320) == StreamQuality.MP3_320
    assert track.query_quality(StreamQuality.FLAC) == StreamQuality.MP3_320


def test_track_serialize(configured_onzr, responses):
    """Test the Track serialization."""
    track_id = 1
    track_token = "fake"  # noqa: S105
    track_duration = 120
    track_artist = "Jimi Hendrix"
    track_title = "All along the watchtower"
    track_album = "Experience"
    track_picture = "ABCDEF"

    responses.post(
        "http://www.deezer.com/ajax/gw-light.php",
        status=200,
        json=DeezerSongResponseFactory.build(
            error={},
            results=DeezerSongFactory.build(
                SNG_ID=track_id,
                TRACK_TOKEN=track_token,
                DURATION=track_duration,
                ART_NAME=track_artist,
                SNG_TITLE=track_title,
                VERSION="",
                ALB_TITLE=track_album,
                ALB_PICTURE=track_picture,
            ),
        ).model_dump(),
    )

    track = Track(client=configured_onzr.deezer, track_id=track_id, background=False)

    assert track.serialize() == TrackShort(
        id=track_id,
        title=track_title,
        album=track_album,
        artist=track_artist,
    )
