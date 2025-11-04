"""Onzr: deezer client."""

import functools
import hashlib
import logging
from enum import IntEnum
from threading import Thread
from typing import Any, Generator, Iterator, List, Optional, no_type_check

import deezer
import requests
from Cryptodome.Cipher import Blowfish
from pydantic import HttpUrl

from .exceptions import DeezerTrackException
from .models import (
    AlbumShort,
    ArtistShort,
    Collection,
    StreamQuality,
    TrackInfo,
    TrackShort,
)

logger = logging.getLogger(__name__)


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
                id=track.get("id"),
                title=track.get("title"),
                album=track.get("album").get("title"),
                artist=track.get("artist").get("name"),
            )

    @staticmethod
    def _to_albums(data, artist: ArtistShort) -> Generator[AlbumShort, None, None]:
        """API results to AlbumShort."""
        for album in data:
            logger.debug(f"{album=}")
            yield AlbumShort(
                id=album.get("id"),
                title=album.get("title"),
                release_date=album.get("release_date"),
                artist=artist.name,
            )

    def artist(
        self,
        artist_id: int,
        radio: bool = False,
        top: bool = True,
        albums: bool = False,
        limit: int = 10,
    ) -> List[TrackShort] | List[AlbumShort]:
        """Get artist tracks."""
        response = self.api.get_artist(artist_id)
        artist = ArtistShort(id=response.get("id"), name=response.get("name"))
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

    def album(self, album_id: int) -> List[TrackShort]:
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
                    id=a.get("id"),
                    name=a.get("name"),
                )
                for a in response["data"]
            ]
        elif album:
            response = self.api.search_album(album)
            results = [
                AlbumShort(
                    id=a.get("id"),
                    title=a.get("title"),
                    release_date=a.get("release_date"),
                    artist=a.get("artist").get("name"),
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


class AlbumCoverSize(IntEnum):
    """Album cover sizes."""

    SMALL = 0
    MEDIUM = 1
    BIG = 2
    XL = 3


def get_album_cover_filename(size: AlbumCoverSize) -> str:
    """Get album cover filename given its size."""
    match size:
        case AlbumCoverSize.SMALL:
            return "56x56-000000-80-0-0.jpg"
        case AlbumCoverSize.MEDIUM:
            return "250x250-000000-80-0-0.jpg"
        case AlbumCoverSize.BIG:
            return "500x500-000000-80-0-0.jpg"
        case AlbumCoverSize.XL:
            return "1000x1000-000000-80-0-0.jpg"


class Track:
    """A Deezer track."""

    def __init__(
        self,
        client: DeezerClient,
        track_id: int,
        background: bool = False,
    ) -> None:
        """Instantiate a new track."""
        self.deezer = client
        self.track_id = track_id
        self.session = requests.Session()

        self.track_info: Optional[TrackInfo] = None
        # Fetch track info in a separated thread to make instantiation non-blocking
        if background:
            thread = Thread(target=self._set_track_info)
            thread.start()
        else:
            self._set_track_info()

        self.key: bytes = self._generate_blowfish_key()
        self.status: TrackStatus = TrackStatus.IDLE
        self.streamed: int = 0

    def __str__(self) -> str:
        """Get track str representation."""
        return f"ID: {self.track_id}"

    def _set_track_info(self):
        """Get track info."""
        track_info = self.deezer.gw.get_track(self.track_id)
        logger.debug("Track info: %s", track_info)
        filesizes = {
            "FILESIZE_MP3_128": StreamQuality.MP3_128,
            "FILESIZE_MP3_320": StreamQuality.MP3_320,
            "FILESIZE_FLAC": StreamQuality.FLAC,
        }
        self.track_info = TrackInfo(
            id=track_info["SNG_ID"],
            token=track_info["TRACK_TOKEN"],
            duration=track_info["DURATION"],
            artist=track_info["ART_NAME"],
            title=(
                f"{track_info['SNG_TITLE']} {track_info['VERSION']}"
                if "VERSION" in track_info and track_info["VERSION"]
                else track_info["SNG_TITLE"]
            ),
            album=track_info["ALB_TITLE"],
            picture=track_info["ALB_PICTURE"],
            formats=[
                filesizes[size] for size in filesizes if int(track_info[size]) > 0
            ],
        )
        if not len(self.formats):
            raise DeezerTrackException(
                f"No available formats detected for track {self.track_id}"
            )
        logger.debug(f"{self.track_info}")

    def refresh(self):
        """Refresh track info."""
        logger.debug("Refreshing track info…")
        self._set_track_info()

    def _get_url(self, quality: StreamQuality) -> str:
        """Get URL of the track to stream."""
        logger.debug(f"Getting track url with quality {quality}…")
        url = self.deezer.get_track_url(self.token, quality.value)
        return url

    def _generate_blowfish_key(self) -> bytes:
        """Generate the blowfish key for Deezer downloads.

        Taken from: https://github.com/nathom/streamrip/
        """
        md5_hash = hashlib.md5(str(self.track_id).encode()).hexdigest()  # noqa: S324
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

    def _get_track_info_attribute(self, field: str) -> Any:
        """Get self.track_info attribute if defined."""
        if self.track_info is None:
            return "fetching…"
        return getattr(self.track_info, field, "missing info")

    @property
    def token(self) -> str:
        """Get track token."""
        return self._get_track_info_attribute("token")

    @property
    def duration(self) -> int:
        """Get track duration (in seconds)."""
        return self._get_track_info_attribute("duration")

    @property
    def artist(self) -> str:
        """Get track artist."""
        return self._get_track_info_attribute("artist")

    @property
    def title(self) -> str:
        """Get track title."""
        return self._get_track_info_attribute("title")

    @property
    def album(self) -> str:
        """Get track album."""
        return self._get_track_info_attribute("album")

    @property
    def formats(self) -> List[StreamQuality]:
        """Get track formats."""
        return self._get_track_info_attribute("formats") or []

    def query_quality(self, quality: StreamQuality) -> StreamQuality:
        """Get track quality among available formats.

        All stream qualities are not available for every tracks, if queried quality
        is not available return the best available quality among supported formats.
        """
        if quality in self.formats:
            return quality
        return self.formats[-1]

    @property
    def picture(self) -> str | None:
        """Get track picture."""
        return self._get_track_info_attribute("picture")

    def _cover(self, size: AlbumCoverSize) -> HttpUrl | None:
        """Get track album cover URL given requested size."""
        return (
            HttpUrl(
                "https://e-cdns-images.dzcdn.net/images/cover/"
                f"{self.picture}/"
                f"{get_album_cover_filename(size)}"
            )
            if self.picture
            else None
        )

    @property
    def cover_small(self) -> HttpUrl | None:
        """Get small album cover URL."""
        return self._cover(AlbumCoverSize.SMALL)

    @property
    def cover_medium(self) -> HttpUrl | None:
        """Get medium album cover URL."""
        return self._cover(AlbumCoverSize.MEDIUM)

    @property
    def cover_big(self) -> HttpUrl | None:
        """Get big album cover URL."""
        return self._cover(AlbumCoverSize.BIG)

    @property
    def cover_xl(self) -> HttpUrl | None:
        """Get XL album cover URL."""
        return self._cover(AlbumCoverSize.XL)

    @property
    def full_title(self) -> str:
        """Get track full title (artist/title/album)."""
        return f"{self.artist} - {self.title} [{self.album}]"

    def stream(self, quality: StreamQuality = StreamQuality.MP3_128) -> Iterator[bytes]:
        """Fetch track in-memory.

        quality (StreamQuality): audio file to stream quality
        """
        if (best := self.query_quality(quality)) != quality:
            logger.warning(
                (
                    "Required track quality %s is not available. Will try best "
                    "available format instead: %s"
                ),
                quality,
                best,
            )
            quality = best

        logger.debug(
            "Start streaming track: "
            f"▶️ {self.full_title} (ID: {self.track_id} Q: {quality})"
        )

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
        logger.debug(f"Track fully streamed {self.streamed}")

    # Pydantic will raise an error for us
    @no_type_check
    def serialize(self) -> TrackShort:
        """Serialize current track."""
        return TrackShort(
            id=self.track_id,
            title=self.title,
            album=self.album,
            artist=self.artist,
        )
