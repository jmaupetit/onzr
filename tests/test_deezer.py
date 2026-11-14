"""Onzr deezer tests."""

import concurrent.futures
import datetime
import json
from time import sleep

import pytest
from pydantic import HttpUrl
from responses import matchers

from onzr.deezer import (
    AlbumSortBy,
    DeezerClient,
    StreamQuality,
    Track,
    TrackSortBy,
    TrackStatus,
)
from onzr.exceptions import DeezerTrackException
from onzr.models.core import (
    AlbumShort,
    ArtistShort,
    PlaylistShort,
    TrackInfo,
    TrackShort,
)
from onzr.models.deezer import (
    DeezerAPIResponseCollection,
    DeezerGWPlaylist,
    DeezerSong,
    DeezerUserProfilePagePlaylists,
)
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
    DeezerFavoriteFactory,
    DeezerFavoriteResponseFactory,
    DeezerGWPlaylistFactory,
    DeezerGWPlaylistResponseFactory,
    DeezerPlaylistFactory,
    DeezerSearchAlbumResponseFactory,
    DeezerSearchArtistResponseFactory,
    DeezerSearchPlaylistResponseFactory,
    DeezerSearchTrackResponseFactory,
    DeezerSongFactory,
    DeezerSongResponseFactory,
    DeezerTrackFactory,
    DeezerUserProfilePageTabPlaylistsFactory,
    TrackShortFactory,
)

PAGE_PROFILE_MATCHER = matchers.query_param_matcher(
    {"method": "deezer.pageProfile"}, strict_match=False
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
    assert client.connection_pool_maxsize == expected
    # Both the standard API (https) and the gateway API (http) use the pool
    for url in ("https://api.deezer.com", "http://www.deezer.com"):
        assert client.session.get_adapter(url) is client.adapter
    assert client.adapter._pool_maxsize == expected


@pytest.fixture
def executor_workers(monkeypatch):
    """Record the `max_workers` of thread pools created by the Deezer client."""
    workers = []
    executor_class = concurrent.futures.ThreadPoolExecutor

    def executor(*args, **kwargs):
        workers.append(kwargs.get("max_workers"))
        return executor_class(*args, **kwargs)

    monkeypatch.setattr("onzr.deezer.concurrent.futures.ThreadPoolExecutor", executor)
    return workers


def test_deezer_client_collection_details(responses, deezer_client, executor_workers):
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
    # Ensure concurrency is bounded by the connection pool size
    assert executor_workers == [deezer_client.connection_pool_maxsize]

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

    # Items that cannot be fetched are dropped
    tracks = [TrackShortFactory.build(id=i) for i in (1, 42, 3)]
    for track_id in (1, 3):
        responses.get(
            f"https://api.deezer.com/track/{track_id}",
            status=200,
            json=json.loads(DeezerTrackFactory.build(id=track_id).model_dump_json()),
        )
    responses.get(
        "https://api.deezer.com/track/42",
        status=200,
        json={"error": {"code": 800, "type": "DataException", "message": "no data"}},
    )
    tracks = deezer_client._collection_details(tracks)
    assert [t.id for t in tracks] == [1, 3]

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
    artist = DeezerArtistFactory.build(id=artist_id)
    responses.get(
        f"https://api.deezer.com/artist/{artist_id}",
        status=200,
        json=json.loads(artist.model_dump_json()),
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
    # The API does not include the artist in artist albums
    payload = DeezerArtistAlbumsResponseFactory.build(
        data=[DeezerAlbumFactory.build(artist=None) for _ in range(2)]
    )
    responses.get(
        f"https://api.deezer.com/artist/{artist_id}/albums",
        status=200,
        json=json.loads(payload.model_dump_json()),
    )
    albums = deezer_client.artist(
        artist_id=artist_id, radio=False, top=False, albums=True
    )
    assert isinstance(albums[0], AlbumShort)
    assert len(albums) == len(payload.data)
    assert all(a.artist == artist.name for a in albums)


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


def test_deezer_client_playlist(responses, deezer_client):
    """Test the DeezerClient `playlist` method."""
    playlist_id = 666

    payload = DeezerPlaylistFactory.build(id=playlist_id)
    responses.get(
        f"https://api.deezer.com/playlist/{playlist_id}",
        status=200,
        json=json.loads(payload.model_dump_json()),
    )
    playlist = deezer_client.playlist(playlist_id=playlist_id)
    assert isinstance(playlist, PlaylistShort)
    assert playlist.id == playlist_id


def test_deezer_client_private_playlist(responses, deezer_client):
    """Test the DeezerClient `playlist` method with a private playlist.

    Private playlists are not accessible using the standard API: a PermissionException
    is raised. Then a fallback on the gateway API allows us to get playlist details
    and its tracks.
    """
    playlist_id = 666

    # First call: standard API raises a permission error
    responses.get(
        f"https://api.deezer.com/playlist/{playlist_id}",
        status=200,
        json={"error": {"code": 200, "type": "Exception", "message": "no permission"}},
    )
    # Second call: gateway API provides playlist details (10 first tracks)
    payload = DeezerGWPlaylistResponseFactory.build(
        DATA=DeezerGWPlaylistFactory.build(
            PLAYLIST_ID=playlist_id, TITLE="Private playlist", STATUS=1
        ),
        SONGS=DeezerAPIResponseCollection[DeezerSong](data=[]),
    )
    responses.post(
        "http://www.deezer.com/ajax/gw-light.php",
        status=200,
        json={"error": {}, "results": json.loads(payload.model_dump_json())},
    )
    # Third call: gateway API provides all playlist tracks
    payload = DeezerSongFactory.build(SNG_ID=1, VERSION=None)
    responses.post(
        "http://www.deezer.com/ajax/gw-light.php",
        status=200,
        json={
            "error": {},
            "results": {"data": [json.loads(payload.model_dump_json())]},
        },
    )

    playlist = deezer_client.playlist(playlist_id=playlist_id)
    assert isinstance(playlist, PlaylistShort)
    assert playlist.id == playlist_id
    assert playlist.public is False
    assert [t.id for t in playlist.tracks] == [1]


def test_deezer_client_user(deezer_client, deezer_user):
    """Test the DeezerClient `user` property."""
    assert deezer_client.user == deezer_user


def test_deezer_client_user_playlists(responses, deezer_client, deezer_user):
    """Test the DeezerClient `user_playlists` method."""
    # The user name is used as a fallback for playlist owner
    playlists = DeezerUserProfilePageTabPlaylistsFactory.build(
        TAB=DeezerUserProfilePagePlaylists(
            playlists=DeezerAPIResponseCollection[DeezerGWPlaylist](
                data=[
                    DeezerGWPlaylistFactory.build(
                        PLAYLIST_ID=1,
                        TITLE="Public",
                        STATUS=0,
                        PARENT_USERNAME=None,
                    ),
                    DeezerGWPlaylistFactory.build(
                        PLAYLIST_ID=2,
                        TITLE="Private",
                        STATUS=1,
                        PARENT_USERNAME=None,
                    ),
                ]
            )
        )
    )
    responses.post(
        "http://www.deezer.com/ajax/gw-light.php",
        status=200,
        match=[PAGE_PROFILE_MATCHER],
        json={"error": {}, "results": json.loads(playlists.model_dump_json())},
    )

    playlists = deezer_client.user_playlists()
    assert [p.id for p in playlists] == [1, 2]
    assert [p.user for p in playlists] == [deezer_user.name, deezer_user.name]

    private_playlists = deezer_client.user_playlists(private=True)
    assert [p.id for p in private_playlists] == [2]


def test_deezer_client_user_artists(responses, deezer_client):
    """Test the DeezerClient `user_artists` method."""
    # The gateway user artists response follows the user profile page format
    responses.post(
        "http://www.deezer.com/ajax/gw-light.php",
        status=200,
        match=[PAGE_PROFILE_MATCHER],
        json={
            "error": {},
            "results": {
                "TAB": {
                    "artists": {
                        "data": [
                            {"ART_ID": 2, "ART_NAME": "Zed", "NB_FAN": 1},
                            {"ART_ID": 1, "ART_NAME": "Alice", "NB_FAN": 2},
                            {"ART_ID": 3, "ART_NAME": "bob", "NB_FAN": 3},
                        ]
                    }
                }
            },
        },
    )

    artists = deezer_client.user_artists()
    # Ensure artists are sorted by name (case-insensitive)
    assert [a.name for a in artists] == ["Alice", "bob", "Zed"]


def test_deezer_client_user_albums(responses, deezer_client):
    """Test the DeezerClient `user_albums` method."""
    # The gateway user albums response follows the user profile page format
    responses.post(
        "http://www.deezer.com/ajax/gw-light.php",
        status=200,
        match=[PAGE_PROFILE_MATCHER],
        json={
            "error": {},
            "results": {
                "TAB": {
                    "albums": {
                        "data": [
                            {
                                "ALB_ID": 2,
                                "ALB_TITLE": "Zed",
                                "ALB_PICTURE": "pic",
                                "ART_ID": 2,
                                "ART_NAME": "Zed",
                                "EXPLICIT_ALBUM_CONTENT": {"EXPLICIT_LYRICS_STATUS": 0},
                            },
                            {
                                "ALB_ID": 1,
                                "ALB_TITLE": "Alice",
                                "ALB_PICTURE": "pic",
                                "ART_ID": 1,
                                "ART_NAME": "Alice",
                                "EXPLICIT_ALBUM_CONTENT": {"EXPLICIT_LYRICS_STATUS": 0},
                            },
                            {
                                "ALB_ID": 3,
                                "ALB_TITLE": "beta",
                                "ALB_PICTURE": "pic",
                                "ART_ID": 3,
                                "ART_NAME": "",
                                "EXPLICIT_ALBUM_CONTENT": {"EXPLICIT_LYRICS_STATUS": 0},
                            },
                            {
                                "ALB_ID": 4,
                                "ALB_TITLE": "Omega",
                                "ALB_PICTURE": "pic",
                                "ART_ID": 4,
                                "ART_NAME": "dEUS",
                                "EXPLICIT_ALBUM_CONTENT": {"EXPLICIT_LYRICS_STATUS": 0},
                            },
                        ]
                    }
                }
            },
        },
    )

    # Ensure albums are sorted by title (case-insensitive)
    albums = deezer_client.user_albums(sort_by=AlbumSortBy.TITLE)
    assert [a.title for a in albums] == ["Alice", "beta", "Omega", "Zed"]

    # Ensure albums are sorted by artist, albums without artist last
    albums = deezer_client.user_albums(sort_by=AlbumSortBy.ARTIST)
    assert [a.artist for a in albums] == ["Alice", "dEUS", "Zed", ""]


def test_deezer_client_user_tracks(responses, deezer_client, executor_workers):
    """Test the DeezerClient `user_tracks` method."""
    gw_url = "http://www.deezer.com/ajax/gw-light.php"

    def favorites(song_id: int, start: int):
        payload = DeezerFavoriteResponseFactory.build(
            data=[DeezerFavoriteFactory.build(SNG_ID=song_id)], total=2
        )
        responses.post(
            gw_url,
            status=200,
            match=[
                matchers.query_param_matcher(
                    {"method": "song.getFavoriteIds"}, strict_match=False
                ),
                matchers.json_params_matcher(
                    {"nb": 1, "start": start}, strict_match=False
                ),
            ],
            json={"error": {}, "results": json.loads(payload.model_dump_json())},
        )

    def songs(song_id: int):
        payload = DeezerSongFactory.build(SNG_ID=song_id, VERSION=None)
        responses.post(
            gw_url,
            status=200,
            match=[
                matchers.query_param_matcher(
                    {"method": "song.getListData"}, strict_match=False
                ),
                matchers.json_params_matcher({"SNG_IDS": [song_id]}),
            ],
            json={
                "error": {},
                "results": {"data": [json.loads(payload.model_dump_json())]},
            },
        )

    # Two pages of one favorite each: pagination stops once `total` is reached
    favorites(1, start=0)
    songs(1)
    favorites(2, start=1)
    songs(2)

    tracks = list(deezer_client.user_tracks(page_size=1))
    assert [t.id for t in tracks] == [1, 2]
    # Ignore the gateway token request
    methods = [
        c.request.params["method"]
        for c in responses.calls
        if c.request.params["method"] != "deezer.getUserData"
    ]
    assert methods == ["song.getFavoriteIds", "song.getListData"] * 2
    # One bounded thread pool per page
    assert executor_workers == [deezer_client.connection_pool_maxsize] * 2


@pytest.mark.parametrize(
    "sort_by,expected",
    [
        (None, [1, 2, 3]),
        (TrackSortBy.ALBUM, [3, 1, 2]),
        (TrackSortBy.ARTIST, [2, 3, 1]),
        (TrackSortBy.TITLE, [1, 2, 3]),
    ],
)
def test_deezer_client_user_tracks_sort_by(
    monkeypatch, deezer_client, sort_by, expected
):
    """Test the DeezerClient `user_tracks` method sorting (case-insensitive)."""
    tracks = [
        TrackShort(id=1, title="alpha", album="Zulu", artist="zed"),
        TrackShort(id=2, title="Bravo", album="zz top", artist="Abba"),
        TrackShort(id=3, title="charlie", album="Alpha", artist="beatles"),
    ]
    monkeypatch.setattr(
        DeezerClient, "_iter_user_tracks", lambda *args, **kwargs: iter(tracks)
    )

    result = deezer_client.user_tracks(page_size=1, sort_by=sort_by)
    assert [t.id for t in result] == expected


def test_deezer_client_user_tracks_empty(responses, deezer_client):
    """Test the DeezerClient `user_tracks` method with no favorites."""
    payload = DeezerFavoriteResponseFactory.build(data=[], total=0)
    responses.post(
        "http://www.deezer.com/ajax/gw-light.php",
        status=200,
        json={"error": {}, "results": json.loads(payload.model_dump_json())},
    )

    assert list(deezer_client.user_tracks(page_size=1)) == []
    # Ignore the gateway token request
    methods = [
        c.request.params["method"]
        for c in responses.calls
        if c.request.params["method"] != "deezer.getUserData"
    ]
    assert methods == ["song.getFavoriteIds"]


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

    # Playlist
    payload = DeezerSearchPlaylistResponseFactory.build()
    responses.get(
        "https://api.deezer.com/search/playlist",
        status=200,
        json=json.loads(payload.model_dump_json()),
    )
    playlists = deezer_client.search(playlist="jazz")
    assert isinstance(playlists[0], PlaylistShort)
    assert len(playlists) == len(payload.data)


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
