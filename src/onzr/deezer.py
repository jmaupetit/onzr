"""Onzr: deezer client."""

import functools
import hashlib
import logging
from dataclasses import asdict, dataclass
from enum import IntEnum, StrEnum
from threading import Thread
from typing import Generator, List, Optional, Protocol

import deezer
import requests
from Cryptodome.Cipher import Blowfish

logger = logging.getLogger(__name__)


class StreamQuality(StrEnum):
    """Track stream quality."""

    MP3_128 = "MP3_128"
    MP3_320 = "MP3_320"
    FLAC = "FLAC"

    @property
    def media_type(self) -> str:
        """Get media type corresponding to selected quality."""
        if self == StreamQuality.FLAC:
            return "audio/flac"
        return "audio/mpeg"


@dataclass
class IsDataclassProtocol(Protocol):
    """A protocol to type check dataclass mixins."""


class ToListMixin(IsDataclassProtocol):
    """A dataclass mixin that converts all fields values to a list."""

    def _dataclass_to_list(self, target=None) -> List[str | List]:
        """Convert all field values to a list."""
        if target is None:
            target = asdict(self)
        return [
            v if not isinstance(v, dict) else self._dataclass_to_list(v)
            for v in target.values()
        ]

    def to_list(self, target: List[str | List] | None = None) -> List[str]:
        """Convert nested dataclasses to values list."""
        if target is None:
            target = self._dataclass_to_list()
        out = []
        for i in target:
            if isinstance(i, list):
                out += self.to_list(i)
            # Ignore None
            elif i:
                out.append(i)
        return out


@dataclass
class ArtistShort(ToListMixin):
    """A small model to represent an artist."""

    id: str
    name: str


@dataclass
class AlbumShort(ToListMixin):
    """A small model to represent an artist."""

    id: str
    name: str
    release_date: Optional[str] = None
    artist: Optional[ArtistShort] = None


@dataclass
class TrackShort(ToListMixin):
    """A small model to represent an artist."""

    id: str
    title: str
    album: AlbumShort


Collection = List[ArtistShort] | List[AlbumShort] | List[TrackShort]


class DeezerClient(deezer.Deezer):
    """A wrapper for the Deezer API client."""

    def __init__(
        self,
        arl: str,
        blowfish: str,
        fast: bool = False,
    ) -> None:
        """Instantiate the Deezer API client.

        Fast login is useful to quicky access some API endpoints such as "search" but
        won't work if you need to stream tracks.
        """
        super().__init__()

        self.arl = arl
        self.blowfish = blowfish
        if fast:
            self._fast_login()
        else:
            self._login()

    def _login(self):
        """Login to deezer API."""
        logger.debug("Login in to deezer using defined ARL…")
        self.login_via_arl(self.arl)

    def _fast_login(self):
        """Fasting login using ARL cookie."""
        cookie_obj = requests.cookies.create_cookie(
            domain=".deezer.com",
            name="arl",
            value=self.arl,
            path="/",
            rest={"HttpOnly": True},
        )
        self.session.cookies.set_cookie(cookie_obj)
        self.logged_in = True

    @staticmethod
    def _to_tracks(data) -> Generator[TrackShort, None, None]:
        """API results to TrackShort."""
        for track in data:
            yield TrackShort(
                id=str(track.get("id")),
                title=track.get("title"),
                album=AlbumShort(
                    id=str(track.get("album").get("id")),
                    name=track.get("album").get("title"),
                    release_date=track.get("album").get("release_date"),
                    artist=ArtistShort(
                        id=str(track.get("artist").get("id")),
                        name=track.get("artist").get("name"),
                    ),
                ),
            )

    def _to_albums(
        self, data, artist: ArtistShort
    ) -> Generator[AlbumShort, None, None]:
        """API results to AlbumShort."""
        for album in data:
            logger.debug(f"{album=}")
            yield AlbumShort(
                id=str(album.get("id")),
                name=album.get("title"),
                release_date=album.get("release_date"),
                artist=artist,
            )

    def artist(
        self,
        artist_id: str,
        radio: bool = False,
        top: bool = True,
        albums: bool = False,
        limit: int = 10,
    ) -> List[TrackShort] | List[AlbumShort]:
        """Get artist tracks."""
        response = self.api.get_artist(artist_id)
        artist = ArtistShort(id=str(response.get("id")), name=response.get("name"))
        logger.debug(f"{artist=}")

        if radio:
            response = self.api.get_artist_radio(artist_id, limit=limit)
            return list(self._to_tracks(response["data"]))
        elif top:
            response = self.api.get_artist_top(artist_id, limit=limit)
            return list(self._to_tracks(response["data"]))
        elif albums:
            response = self.api.get_artist_albums(artist_id, limit=limit)
            return list(self._to_albums(response["data"], artist))
        else:
            raise ValueError(
                "Either radio, top or albums should be True to get artist details"
            )

    def album(self, album_id: str) -> List[TrackShort]:
        """Get album tracks."""
        response = self.api.get_album(album_id)
        logger.debug(f"{response=}")
        return list(self._to_tracks(response["tracks"]["data"]))

    def search(
        self,
        artist: str = "",
        album: str = "",
        track: str = "",
        strict: bool = False,
    ) -> Collection:
        """Mixed custom search."""
        results: Collection = []

        if len(list(filter(None, (artist, album, track)))) > 1:
            response = self.api.advanced_search(
                artist=artist, album=album, track=track, strict=strict
            )
            results = list(self._to_tracks(response["data"]))
        elif artist:
            response = self.api.search_artist(artist)
            results = [
                ArtistShort(
                    id=str(a.get("id")),
                    name=a.get("name"),
                )
                for a in response["data"]
            ]
        elif album:
            response = self.api.search_album(album)
            results = [
                AlbumShort(
                    id=str(a.get("id")),
                    name=a.get("title"),
                    release_date=a.get("release_date"),
                    artist=ArtistShort(
                        id=str(a.get("artist").get("id")),
                        name=str(a.get("artist").get("name")),
                    ),
                )
                for a in response["data"]
            ]
        elif track:
            response = self.api.search_track(track)
            results = list(self._to_tracks(response["data"]))

        return results


class TrackStatus(IntEnum):
    """Track statuses."""

    IDLE = 1
    STREAMING = 2
    STREAMED = 3


class Track:
    """A Deezer track."""

    def __init__(
        self,
        client: DeezerClient,
        track_id: str,
        background: bool = False,
    ) -> None:
        """Instantiate a new track."""
        self.deezer = client
        self.track_id = track_id
        self.session = requests.Session()

        self.track_info: dict = {}
        # Fetch track info in a separated thread to make instantiation non-blocking
        if background:
            thread = Thread(target=self._set_track_info)
            thread.start()
        else:
            self._set_track_info()

        self.key: bytes = self._generate_blowfish_key()
        self.status: TrackStatus = TrackStatus.IDLE
        self.streamed: int = 0

    def _set_track_info(self):
        """Get track info."""
        track_info = self.deezer.gw.get_track(self.track_id)
        logger.debug("Track info: %s", track_info)
        self.track_info = track_info

    def _get_url(self, quality: StreamQuality) -> str:
        """Get URL of the track to stream."""
        logger.debug(f"Getting track url with quality {quality}…")
        url = self.deezer.get_track_url(self.token, quality.value)
        return url

    def _generate_blowfish_key(self) -> bytes:
        """Generate the blowfish key for Deezer downloads.

        Taken from: https://github.com/nathom/streamrip/
        """
        md5_hash = hashlib.md5(self.track_id.encode()).hexdigest()  # noqa: S324
        # good luck :)
        return "".join(
            chr(functools.reduce(lambda x, y: x ^ y, map(ord, t)))
            for t in zip(
                md5_hash[:16],
                md5_hash[16:],
                self.deezer.blowfish,
                strict=False,
            )
        ).encode()

    def _decrypt(self, chunk):
        """Decrypt blowfish encrypted chunk."""
        return Blowfish.new(  # noqa: S304
            self.key,
            Blowfish.MODE_CBC,
            b"\x00\x01\x02\x03\x04\x05\x06\x07",
        ).decrypt(chunk)

    @property
    def token(self) -> str:
        """Get track token."""
        return self.track_info["TRACK_TOKEN"]

    @property
    def duration(self) -> int:
        """Get track duration (in seconds)."""
        return int(self.track_info["DURATION"])

    @property
    def artist(self) -> str:
        """Get track artist."""
        return self.track_info["ART_NAME"]

    @property
    def title(self) -> str:
        """Get track title."""
        return self.track_info["SNG_TITLE"]

    @property
    def album(self) -> str:
        """Get track album."""
        return self.track_info["ALB_TITLE"]

    @property
    def full_title(self) -> str:
        """Get track full title (artist/title/album)."""
        return f"{self.artist} - {self.title} [{self.album}]"

    def as_dict(self):
        """Return dict representation of a Track."""
        return {
            "id": self.track_id,
            "artist": self.artist,
            "album": self.album,
            "title": self.title,
        }

    def stream(self, quality: StreamQuality = StreamQuality.MP3_128):
        """Fetch track in-memory.

        buffer_size (int): the buffer size (defaults to 5 seconds for a 128kbs file)
        """
        logger.debug(f"Start streaming track: {self.track_id} ▶️  {self.full_title}")
        chunk_sep = 2048
        chunk_size = 3 * chunk_sep
        self.streamed = 0
        self.status = TrackStatus.IDLE

        url = self._get_url(quality)
        with self.session.get(url, stream=True) as r:
            r.raise_for_status()
            filesize = int(r.headers.get("Content-Length", 0))
            logger.debug(f"Track size: {filesize}")
            self.status = TrackStatus.STREAMING

            for chunk in r.iter_content(chunk_size):
                if len(chunk) > chunk_sep:
                    dchunk = self._decrypt(chunk[:chunk_sep]) + chunk[chunk_sep:]
                else:
                    dchunk = chunk
                self.streamed += chunk_size
                yield dchunk

        # We are done here
        self.status = TrackStatus.STREAMED
        logger.debug("Track streamed")
