"""Onzr deezer tests."""

import datetime
import json
from time import sleep

import pytest
from pydantic import HttpUrl

from onzr.deezer import DeezerClient, StreamQuality, Track, TrackStatus
from onzr.exceptions import DeezerTrackException
from onzr.models.core import AlbumShort, ArtistShort, TrackInfo, TrackShort
from tests.factories import (
    AlbumShortFactory,
    ArtistShortFactory,
    DeezerAdvancedSearchResponseFactory,
    DeezerAlbumFactory,
    DeezerAlbumResponseFactory,
    DeezerArtistAlbumsResponseFactory,
    DeezerArtistFactory,
    DeezerArtistRadioResponseFactory,
    DeezerArtistTopResponseFactory,
    DeezerSearchAlbumResponseFactory,
    DeezerSearchArtistResponseFactory,
    DeezerSearchTrackResponseFactory,
    DeezerSongFactory,
    DeezerSongResponseFactory,
    DeezerTrackFactory,
    TrackShortFactory,
)


def test_deezer_client_init():
    """Test the DeezerClient init."""
    client = DeezerClient(
        arl="fake",
        blowfish="fake",
        fast=True,
        connection_pool_maxsize=15,
    )

    assert client.arl == "fake"
    assert client.blowfish == "fake"
    expected = 15
    assert client.session.adapters["https://"]._pool_maxsize == expected


def test_deezer_client_collection_details(responses, deezer_client):
    """Test the DeezerClient `_collection_details` method."""
    # Tracks
    tracks = [TrackShortFactory.build(id=i) for i in range(1, 11)]
    for track in tracks:
        responses.get(
            f"https://api.deezer.com/track/{track.id}",
            status=200,
            json=json.loads(DeezerTrackFactory.build(id=track.id).model_dump_json()),
        )
    tracks = deezer_client._collection_details(tracks)
    # Ensure order is preserved
    assert [t.id for t in tracks] == list(range(1, 11))

    # Albums
    albums = [AlbumShortFactory.build(id=i) for i in range(1, 11)]
    for album in albums:
        responses.get(
            f"https://api.deezer.com/album/{album.id}",
            status=200,
            json=json.loads(DeezerAlbumFactory.build(id=album.id).model_dump_json()),
        )
    albums = deezer_client._collection_details(albums)
    # Ensure order is preserved
    assert [t.id for t in albums] == list(range(1, 11))

    # Artists
    artists = [ArtistShortFactory.build(id=i) for i in range(1, 11)]
    with pytest.raises(
        ValueError, match="Input collection should be TrackShort or AlbumShort iterator"
    ):
        deezer_client._collection_details(artists)


def test_deezer_client_artist(responses, deezer_client):
    """Test the DeezerClient `artist` method."""
    artist_id = 1

    # Artist
    payload = DeezerArtistFactory.build(id=artist_id)
    responses.get(
        f"https://api.deezer.com/artist/{artist_id}",
        status=200,
        json=json.loads(payload.model_dump_json()),
    )

    with pytest.raises(
        ValueError,
        match="Either radio, top or albums should be True to get artist details",
    ):
        deezer_client.artist(artist_id=artist_id, radio=False, top=False, albums=False)

    # Radio
    payload = DeezerArtistRadioResponseFactory.build()
    responses.get(
        f"https://api.deezer.com/artist/{artist_id}/radio",
        status=200,
        json=json.loads(payload.model_dump_json()),
    )
    radio = deezer_client.artist(
        artist_id=artist_id, radio=True, top=False, albums=False
    )
    assert isinstance(radio[0], TrackShort)
    assert len(radio) == len(payload.data)

    # Radio - with collection details
    for track in payload.data:
        responses.get(
            f"https://api.deezer.com/track/{track.id}",
            status=200,
            json=json.loads(DeezerTrackFactory.build(id=track.id).model_dump_json()),
        )
    radio = deezer_client.artist(
        artist_id=artist_id,
        radio=True,
        top=False,
        albums=False,
        fetch_release_date=True,
    )
    assert isinstance(radio[0], TrackShort)
    assert len(radio) == len(payload.data)

    # Top
    payload = DeezerArtistTopResponseFactory.build()
    responses.get(
        f"https://api.deezer.com/artist/{artist_id}/top",
        status=200,
        json=json.loads(payload.model_dump_json()),
    )
    radio = deezer_client.artist(
        artist_id=artist_id, radio=False, top=True, albums=False
    )
    assert isinstance(radio[0], TrackShort)
    assert len(radio) == len(payload.data)

    # Albums
    payload = DeezerArtistAlbumsResponseFactory.build()
    responses.get(
        f"https://api.deezer.com/artist/{artist_id}/albums",
        status=200,
        json=json.loads(payload.model_dump_json()),
    )
    radio = deezer_client.artist(
        artist_id=artist_id, radio=False, top=False, albums=True
    )
    assert isinstance(radio[0], AlbumShort)
    assert len(radio) == len(payload.data)


def test_deezer_client_album(responses, deezer_client):
    """Test the DeezerClient `album` method."""
    album_id = 666

    payload = DeezerAlbumResponseFactory.build(id=album_id)
    responses.get(
        f"https://api.deezer.com/album/{album_id}",
        status=200,
        json=json.loads(payload.model_dump_json()),
    )
    tracks = deezer_client.album(album_id=album_id)
    assert isinstance(tracks[0], TrackShort)


def test_deezer_client_track(responses, deezer_client):
    """Test the DeezerClient `track` method."""
    track_id = 666

    payload = DeezerTrackFactory.build(id=track_id)
    responses.get(
        f"https://api.deezer.com/track/{track_id}",
        status=200,
        json=json.loads(payload.model_dump_json()),
    )
    track = deezer_client.track(track_id=track_id)
    assert isinstance(track, TrackShort)
    assert track.id == track_id


def test_deezer_client_search(responses, deezer_client):
    """Test the DeezerClient `search` method."""
    # Missing arguments
    with pytest.raises(
        ValueError, match="You should at least provide one search criterion"
    ):
        deezer_client.search()

    # Advanced search
    payload = DeezerAdvancedSearchResponseFactory.build()
    responses.get(
        "https://api.deezer.com/search",
        status=200,
        json=json.loads(payload.model_dump_json()),
    )
    tracks = deezer_client.search(artist="foo", album="bar")
    assert isinstance(tracks[0], TrackShort)
    assert len(tracks) == len(payload.data)

    # Artists
    payload = DeezerSearchArtistResponseFactory.build()
    responses.get(
        "https://api.deezer.com/search/artist",
        status=200,
        json=json.loads(payload.model_dump_json()),
    )
    artists = deezer_client.search(artist="foo")
    assert isinstance(artists[0], ArtistShort)
    assert len(artists) == len(payload.data)

    # Albums
    payload = DeezerSearchAlbumResponseFactory.build()
    responses.get(
        "https://api.deezer.com/search/album",
        status=200,
        json=json.loads(payload.model_dump_json()),
    )
    albums = deezer_client.search(album="bar")
    assert isinstance(albums[0], AlbumShort)
    assert len(albums) == len(payload.data)

    # Tracks
    payload = DeezerSearchTrackResponseFactory.build()
    responses.get(
        "https://api.deezer.com/search/track",
        status=200,
        json=json.loads(payload.model_dump_json()),
    )
    tracks = deezer_client.search(track="lol")
    assert isinstance(tracks[0], TrackShort)
    assert len(tracks) == len(payload.data)

    # Tracks - with collection details
    for track in payload.data:
        responses.get(
            f"https://api.deezer.com/track/{track.id}",
            status=200,
            json=json.loads(DeezerTrackFactory.build(id=track.id).model_dump_json()),
        )
    tracks = deezer_client.search(track="lol", fetch_release_date=True)
    assert isinstance(tracks[0], TrackShort)
    assert len(tracks) == len(payload.data)


def test_stream_quality_enum():
    """Test the StreamQuality enum."""
    assert StreamQuality.FLAC.media_type == "audio/flac"
    assert StreamQuality.MP3_320.media_type == "audio/mpeg"
    assert StreamQuality.MP3_128.media_type == "audio/mpeg"


def test_track_init(deezer_client, responses):
    """Test the Track instantiation."""
    track_id = 1
    track_token = "fake"  # noqa: S105
    track_duration = 120
    track_artist = "Jimi Hendrix"
    track_title = "All along the watchtower"
    track_version = "(Dylan remix)"
    track_album = "Experience"
    track_picture = "ABCDEF"
    track_physical_release_date = "2025-01-01"
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
                PHYSICAL_RELEASE_DATE=track_physical_release_date,
                FILESIZE_MP3_128=track_filesize_mp3_128,
                FILESIZE_MP3_320=track_filesize_mp3_320,
                FILESIZE_FLAC=track_filesize_flac,
            ),
        ).model_dump(),
    )

    track = Track(client=deezer_client, track_id=track_id, background=False)

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
        release_date=track_physical_release_date,
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
    assert track.release_date == datetime.date(2025, 1, 1)
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
    assert str(track) == "ID: 1"

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
                PHYSICAL_RELEASE_DATE=track_physical_release_date,
                FILESIZE_MP3_128=track_filesize_mp3_128,
                FILESIZE_MP3_320=track_filesize_mp3_320,
                FILESIZE_FLAC=0,
            ),
        ).model_dump(),
    )
    track = Track(client=deezer_client, track_id=track_id, background=False)

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
                PHYSICAL_RELEASE_DATE=track_physical_release_date,
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
        Track(client=deezer_client, track_id=track_id, background=False)

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
                PHYSICAL_RELEASE_DATE=track_physical_release_date,
                FILESIZE_MP3_128=track_filesize_mp3_128,
                FILESIZE_MP3_320=track_filesize_mp3_320,
                FILESIZE_FLAC=track_filesize_flac,
            ),
        ).model_dump(),
    )

    track = Track(client=deezer_client, track_id=track_id, background=False)
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
            PHYSICAL_RELEASE_DATE=track_physical_release_date,
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

    track = Track(client=deezer_client, track_id=track_id, background=False)
    assert track.title == track_title

    # Background init
    track = Track(client=deezer_client, track_id=track_id, background=True)
    sleep(0.5)
    assert track.title == track_title


def test_track_fallback(deezer_client, responses):
    """Test track fallback.

    When a track is no longer available or restricted in some country, a fallback track
    is proposed in the track payload. We decide then to switch the initial reference by
    the proposed fallback.
    """
    track_id = 1
    track_token = "fake"  # noqa: S105
    track_duration = 120
    track_artist = "Jimi Hendrix"
    track_title = "All along the watchtower"
    track_album = "Experience"
    track_picture = "ABCDEF"
    track_physical_release_date = "2025-01-01"
    track_filesize_mp3_128 = 128
    track_filesize_mp3_320 = 320
    track_filesize_flac = 0

    fallback_track_id = 2
    fallback_track_filesize_flac = 440

    # Test when a fallback is supplied (field in payload)
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
            PHYSICAL_RELEASE_DATE=track_physical_release_date,
            FILESIZE_MP3_128=track_filesize_mp3_128,
            FILESIZE_MP3_320=track_filesize_mp3_320,
            FILESIZE_FLAC=track_filesize_flac,
            FALLBACK=DeezerSongFactory.build(
                SNG_ID=fallback_track_id,
                TRACK_TOKEN=track_token,
                DURATION=track_duration,
                ART_NAME=track_artist,
                SNG_TITLE=track_title,
                ALB_TITLE=track_album,
                ALB_PICTURE=track_picture,
                PHYSICAL_RELEASE_DATE=track_physical_release_date,
                FILESIZE_MP3_128=track_filesize_mp3_128,
                FILESIZE_MP3_320=track_filesize_mp3_320,
                FILESIZE_FLAC=fallback_track_filesize_flac,
            ),
        ),
    )

    responses.post(
        "http://www.deezer.com/ajax/gw-light.php",
        status=200,
        json=payload.model_dump(),
    )

    track = Track(client=deezer_client, track_id=track_id, background=False)
    assert track.track_id == fallback_track_id
    assert track.formats == [
        StreamQuality.MP3_128,
        StreamQuality.MP3_320,
        StreamQuality.FLAC,
    ]


def test_track_refresh(deezer_client, responses):
    """Test the track `refresh` method."""
    track_id = 1
    track_title = "Paint it black"

    responses.post(
        "http://www.deezer.com/ajax/gw-light.php",
        status=200,
        json=DeezerSongResponseFactory.build(
            error={},
            results=DeezerSongFactory.build(
                SNG_ID=track_id, SNG_TITLE=track_title, VERSION=None
            ),
        ).model_dump(),
    )
    track = Track(client=deezer_client, track_id=track_id, background=False)
    assert track.title == track_title

    new_title = "Paint it white"
    responses.post(
        "http://www.deezer.com/ajax/gw-light.php",
        status=200,
        json=DeezerSongResponseFactory.build(
            error={},
            results=DeezerSongFactory.build(
                SNG_ID=track_id, SNG_TITLE=new_title, VERSION=None
            ),
        ).model_dump(),
    )
    track.refresh()
    assert track.title == new_title


def test_track_get_url(track, monkeypatch):
    """Test the track `_get_url` method."""
    url = "https://fake.example.org/foo/1"
    instance = track(1)
    monkeypatch.setattr(instance.deezer, "get_track_url", lambda x, y: url)
    assert instance._get_url(quality=StreamQuality.MP3_128) == HttpUrl(url)


def test_track_query_quality(deezer_client, responses):
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
                PHYSICAL_RELEASE_DATE="2023-01-01",
                FILESIZE_MP3_128=track_filesize_mp3_128,
                FILESIZE_MP3_320=track_filesize_mp3_320,
                FILESIZE_FLAC=0,
            ),
        ).model_dump(),
    )
    track = Track(client=deezer_client, track_id=track_id, background=False)

    assert track.query_quality(StreamQuality.MP3_128) == StreamQuality.MP3_128
    assert track.query_quality(StreamQuality.MP3_320) == StreamQuality.MP3_320
    assert track.query_quality(StreamQuality.FLAC) == StreamQuality.MP3_320


def test_track_serialize(deezer_client, responses):
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
                PHYSICAL_RELEASE_DATE="2025-01-01",
            ),
        ).model_dump(),
    )

    track = Track(client=deezer_client, track_id=track_id, background=False)

    assert track.serialize() == TrackShort(
        id=track_id,
        title=track_title,
        album=track_album,
        artist=track_artist,
        release_date=datetime.date(2025, 1, 1),
    )
