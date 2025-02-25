"""Onzr: deezer client."""

import functools
import hashlib
import logging
from dataclasses import asdict, dataclass
from enum import IntEnum, StrEnum
from threading import Thread
from time import sleep
from typing import Generator, List, Protocol

import deezer
import requests
from Cryptodome.Cipher import Blowfish

from .config import settings

logger = logging.getLogger(__name__)


class StreamQuality(StrEnum):
    """Track stream quality."""

    MP3_128 = "MP3_128"
    MP3_320 = "MP3_320"
    FLAC = "FLAC"


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
            else:
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
    artist: ArtistShort


@dataclass
class TrackShort(ToListMixin):
    """A small model to represent an artist."""

    id: str
    title: str
    album: AlbumShort


Collection = List[ArtistShort] | list[AlbumShort] | List[TrackShort]


class DeezerClient(deezer.Deezer):
    """A wrapper for the Deezer API client."""

    def __init__(
        self,
        arl: str | None = None,
        quality: StreamQuality | None = None,
        fast: bool = False,
    ) -> None:
        """Instantiate the Deezer API client.

        Fast login is useful to quicky access some API endpoints such as "search" but
        won't work if you need to stream tracks.
        """
        super().__init__()

        self.arl = arl or settings.arl
        self.quality = quality or settings.quality
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
                    artist=ArtistShort(
                        id=str(track.get("artist").get("id")),
                        name=track.get("artist").get("name"),
                    ),
                ),
            )

    def artist(
        self, artist_id: str, radio: bool = False, top: bool = True, limit: int = 10
    ) -> List[TrackShort]:
        """Get artist tracks."""
        if radio:
            response = self.api.get_artist_radio(artist_id, limit=limit)
        elif top:
            response = self.api.get_artist_top(artist_id, limit=limit)
        else:
            raise ValueError("Either radio or top should be True to get artist tracks")

        return list(self._to_tracks(response["data"]))

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
    FETCHING = 2
    PLAYABLE = 3
    FETCHED = 4


class Track:
    """A Deezer track."""

    def __init__(
        self,
        client: DeezerClient,
        track_id: str,
        quality: StreamQuality | None = None,
        buffer: float = 0.5,  # 500ms
    ) -> None:
        """Instantiate a new track."""
        self.deezer = client
        self.track_id = track_id
        self.session = requests.Session()
        self.quality = quality or self.deezer.quality
        self.track_info: dict = self._get_track_info()
        self.url: str = self._get_url()
        self.key: bytes = self._generate_blowfish_key()
        self.status: TrackStatus = TrackStatus.IDLE
        # Content and related memory view will be allocated later (right before fetching
        # the track to decrease memory footprint while adding tracks to queue).
        self.content: bytearray = bytearray()
        self._content_mv: memoryview = memoryview(self.content)
        self.fetched: int = 0
        self.streamed: int = 0
        self.paused: bool = False
        self.bitrate = self.filesize / self.duration
        self.buffer_size: int = int(self.bitrate * buffer)

    def _get_track_info(self) -> dict:
        """Get track info."""
        track_info = self.deezer.gw.get_track(self.track_id)
        logger.debug("Track info: %s", track_info)
        return track_info

    def _get_url(self) -> str:
        """Get URL of the track to stream."""
        logger.debug(f"Getting track url with quality {self.quality}…")
        url = self.deezer.get_track_url(self.token, self.quality.value)
        logger.debug(f"Track url: {url}")
        return url

    def _allocate_content(self) -> None:
        """Allocate memory where we will read/write track bytes."""
        self.content = bytearray(self.filesize)
        self._content_mv = memoryview(self.content)

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
                settings.DEEZER_BLOWFISH_SECRET,
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
    def filesize(self) -> int:
        """Get file size (in bits)."""
        return int(self.track_info[f"FILESIZE_{self.quality}"])

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

    def fetch(self):
        """Fetch track in-memory.

        buffer_size (int): the buffer size (defaults to 5 seconds for a 128kbs file)
        """
        logger.debug(f"Start fetching track with {self.buffer_size=}")
        chunk_sep = 2048
        chunk_size = 3 * chunk_sep
        self.fetched = 0
        self.status = TrackStatus.IDLE
        self._allocate_content()

        with self.session.get(self.url, stream=True) as r:
            r.raise_for_status()
            filesize = int(r.headers.get("Content-Length", 0))
            logger.debug(f"Track size: {filesize} ({self.filesize})")
            self.status = TrackStatus.FETCHING

            for chunk in r.iter_content(chunk_size):
                if len(chunk) > chunk_sep:
                    dchunk = self._decrypt(chunk[:chunk_sep]) + chunk[chunk_sep:]
                else:
                    dchunk = chunk
                self._content_mv[self.fetched : self.fetched + chunk_size] = dchunk
                self.fetched += chunk_size

                if (
                    self.fetched >= self.buffer_size
                    and self.status < TrackStatus.PLAYABLE
                ):
                    logger.debug("Buffering ok")
                    self.status = TrackStatus.PLAYABLE

        # We are done here
        self.status = TrackStatus.FETCHED
        logger.debug("Track fetched")

    def cast(self, socket, chunk_size: int = 1024):
        """Cast the track via UDP using given socket."""
        multicast_group = tuple(settings.MULTICAST_GROUP)
        logger.debug(
            (
                f"Casting from position {self.streamed} with {chunk_size=} "
                f"using socket {socket} "
                f"({multicast_group=})"
            )
        )

        if self.status < TrackStatus.FETCHING:
            logger.debug("Will start fetching content in a new thead…")
            thread = Thread(target=self.fetch)
            thread.start()

        # Wait for the track to be playable
        while self.status < TrackStatus.PLAYABLE:
            sleep(0.01)

        # Sleep time while playing
        wait = 1.0 / (self.bitrate / chunk_size)
        logger.debug(f"Wait time: {wait}s ({self.bitrate=})")

        slow_connection: bool = False
        for start in range(self.streamed, self.filesize, chunk_size):

            # Track has been paused, wait for resume
            while self.paused:
                sleep(0.001)

            # We have buffering issues
            while (self.fetched - start) < self.buffer_size and start < (
                self.filesize - self.buffer_size
            ):
                if not slow_connection:
                    logger.warning(
                        "Slow connection, filling the buffer "
                        f"{self.fetched - self.streamed} < {self.buffer_size}"
                    )
                    logger.debug(
                        f"{start=} | {self.filesize=} | {self.fetched=} | "
                        f"{self.streamed=} | {chunk_size=}"
                    )
                slow_connection = True
                sleep(0.05)
            slow_connection = False

            socket.sendto(self._content_mv[start : start + chunk_size], multicast_group)
            self.streamed += chunk_size
            sleep(wait)
