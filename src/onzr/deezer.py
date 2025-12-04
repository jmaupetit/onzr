"""Onzr: deezer client."""

import functools
import hashlib
import logging
from datetime import date
from enum import IntEnum
from pprint import pformat
from queue import Queue as SyncQueue
from threading import Thread
from typing import Any, Callable, Iterator, List, Optional, cast

import deezer
import requests
from Cryptodome.Cipher import Blowfish
from pydantic import HttpUrl

from onzr.models.deezer import (
    DeezerAdvancedSearchResponse,
    DeezerAlbum,
    DeezerArtist,
    DeezerArtistAlbumsResponse,
    DeezerArtistRadioResponse,
    DeezerArtistResponse,
    DeezerArtistTopResponse,
    DeezerSearchAlbumResponse,
    DeezerSearchArtistResponse,
    DeezerSearchResponse,
    DeezerSearchTrackResponse,
    DeezerSong,
    DeezerTrack,
    to_albums,
    to_artists,
    to_tracks,
)

from .exceptions import DeezerTrackException
from .models.core import (
    AlbumShort,
    Collection,
    StreamQuality,
    TrackInfo,
    TrackShort,
)
from .models.deezer import DeezerAlbumResponse

logger = logging.getLogger(__name__)


class DeezerClient(deezer.Deezer):
    """A wrapper for the Deezer API client."""

    def __init__(
        self,
        arl: str,
        blowfish: str,
        fast: bool = False,
        connection_pool_maxsize: int = 10,
        always_fetch_release_date: bool = False,
    ) -> None:
        """Instantiate the Deezer API client.

        Fast login is useful to quicky access some API endpoints such as "search" but
        won't work if you need to stream tracks.
        """
        super().__init__()

        # Set allowed maximal concurrent connections
        self.adapter = requests.adapters.HTTPAdapter(
            pool_maxsize=connection_pool_maxsize
        )
        self.session.mount("https://", self.adapter)

        self.arl = arl
        self.blowfish = blowfish
        self.always_fetch_release_date = always_fetch_release_date
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

    def _collection_details(
        self,
        collection: Collection,
        # ) -> Generator[TrackShort, None, None] | Generator[AlbumShort, None, None]:
    ) -> Collection:
        """Add detailled informations to collection.

        Detailled informations are fetched using separated threads to speed up response
        time for large collections.
        """
        queue: SyncQueue = SyncQueue()
        threads = []
        order = {}
        endpoint: Callable[[int], TrackShort] | Callable[[int], AlbumShort] | None = (
            None
        )

        def get_track(id_: int) -> TrackShort:
            return cast(
                DeezerTrack, self._api(DeezerTrack, self.api.get_track, id_)
            ).to_short()

        def get_album(id_: int) -> AlbumShort:
            return cast(
                DeezerAlbum, self._api(DeezerAlbum, self.api.get_album, id_)
            ).to_short()

        sample = collection[0]
        if isinstance(sample, TrackShort):
            endpoint = get_track
        elif isinstance(sample, AlbumShort):
            endpoint = get_album
        else:
            msg = "Input collection should be TrackShort or AlbumShort iterator"
            logger.error(msg)
            raise ValueError(msg)

        # Start threads
        # FIXME: mypy cannot reliably guess types when using enumerate
        for position, item in enumerate(collection):
            order[item.id] = position  # type: ignore[attr-defined]
            t = Thread(
                target=lambda q, id_: q.put(endpoint(id_)),
                args=(queue, item.id),  # type: ignore[attr-defined]
            )
            t.start()
            threads.append(t)

        # Join threads
        for t in threads:
            t.join()

        # Get updated collection
        new = []
        while not queue.empty():
            new.append(queue.get())

        # Preserve collection ordering
        return sorted(new, key=lambda i: order[i.id])

    def _api(
        self,
        model: (
            type[DeezerAlbum]
            | type[DeezerAlbumResponse]
            | type[DeezerArtist]
            | type[DeezerArtistResponse]
            | type[DeezerSearchResponse]
            | type[DeezerTrack]
        ),
        endpoint: Callable,
        *args,
        **kwargs,
    ) -> (
        DeezerAlbum
        | DeezerAlbumResponse
        | DeezerArtist
        | DeezerArtistResponse
        | DeezerSearchResponse
        | DeezerTrack
    ):
        """An API proxy that validates response using the input model."""
        logger.debug(f"Will query {endpoint=} to {model=} with {args=}/{kwargs=}")

        response = endpoint(*args, **kwargs)
        logger.debug(f"{pformat(response,sort_dicts=True)=}")

        instance = model(**response)
        logger.debug(f"{instance=}")
        return instance

    def artist(
        self,
        artist_id: int,
        radio: bool = False,
        top: bool = True,
        albums: bool = False,
        limit: int = 10,
        fetch_release_date: bool = False,
    ) -> Collection:
        """Get artist tracks."""
        artist = cast(
            DeezerArtist, self._api(DeezerArtist, self.api.get_artist, artist_id)
        ).to_short()
        logger.debug(f"{artist=}")
        results: Collection = []

        if radio:
            results = list(
                to_tracks(
                    cast(
                        DeezerArtistRadioResponse,
                        self._api(
                            DeezerArtistRadioResponse,
                            self.api.get_artist_radio,
                            artist.id,
                            limit=limit,
                        ),
                    )
                )
            )
        elif top:
            results = list(
                to_tracks(
                    cast(
                        DeezerArtistTopResponse,
                        self._api(
                            DeezerArtistTopResponse,
                            self.api.get_artist_top,
                            artist.id,
                            limit=limit,
                        ),
                    )
                )
            )
        elif albums:
            results = list(
                to_albums(
                    cast(
                        DeezerArtistAlbumsResponse,
                        self._api(
                            DeezerArtistAlbumsResponse,
                            self.api.get_artist_albums,
                            artist.id,
                            limit=limit,
                        ),
                    )
                )
            )
        else:
            raise ValueError(
                "Either radio, top or albums should be True to get artist details"
            )

        if self.always_fetch_release_date or fetch_release_date:
            results = self._collection_details(results)

        return results

    def album(self, album_id: int) -> List[TrackShort]:
        """Get album tracks."""
        return list(
            cast(
                DeezerAlbumResponse,
                self._api(DeezerAlbumResponse, self.api.get_album, album_id),
            ).get_tracks()
        )

    def track(self, track_id: int) -> TrackShort:
        """Get track info."""
        return cast(
            DeezerTrack, self._api(DeezerTrack, self.api.get_track, track_id)
        ).to_short()

    def search(
        self,
        artist: str = "",
        album: str = "",
        track: str = "",
        strict: bool = False,
        fetch_release_date: bool = False,
    ) -> Collection:
        """Mixed custom search."""
        criteria = list(filter(None, (artist, album, track)))
        results: Collection = []

        if len(criteria) == 0:
            msg = "You should at least provide one search criterion"
            logger.error(msg)
            raise ValueError(msg)
        elif len(criteria) > 1:
            results = list(
                to_tracks(
                    cast(
                        DeezerAdvancedSearchResponse,
                        self._api(
                            DeezerAdvancedSearchResponse,
                            self.api.advanced_search,
                            artist=artist,
                            album=album,
                            track=track,
                            strict=strict,
                        ),
                    )
                )
            )
        elif artist:
            results = list(
                to_artists(
                    cast(
                        DeezerSearchArtistResponse,
                        self._api(
                            DeezerSearchArtistResponse, self.api.search_artist, artist
                        ),
                    )
                )
            )
        elif album:
            results = list(
                to_albums(
                    cast(
                        DeezerSearchAlbumResponse,
                        self._api(
                            DeezerSearchAlbumResponse, self.api.search_album, album
                        ),
                    )
                )
            )
        elif track:
            results = list(
                to_tracks(
                    cast(
                        DeezerSearchTrackResponse,
                        self._api(
                            DeezerSearchTrackResponse, self.api.search_track, track
                        ),
                    ),
                )
            )

        if (self.always_fetch_release_date or fetch_release_date) and not artist:
            results = self._collection_details(results)

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
        self.key: Optional[bytes] = None

        # Fetch track info in a separated thread to make instantiation non-blocking
        if background:
            thread = Thread(target=self._set_track_info)
            thread.start()
        else:
            self._set_track_info()

        self.status: TrackStatus = TrackStatus.IDLE
        self.streamed: int = 0

    def __str__(self) -> str:
        """Get track str representation."""
        return f"ID: {self.track_id}"

    def _set_track_info(self):
        """Get track info."""
        self.track_info = DeezerSong(
            **self.deezer.gw.get_track(self.track_id)
        ).to_track_info()
        logger.debug("Track info: %s", pformat(self.track_info, sort_dicts=True))

        self.track_id = self.track_info.id
        self.key = self._generate_blowfish_key()
        if not len(self.track_info.formats):
            raise DeezerTrackException(
                f"No available formats detected for track {self.track_id}"
            )
        logger.debug(f"{self.track_info}")

    def refresh(self):
        """Refresh track info."""
        logger.debug("Refreshing track info…")
        self._set_track_info()

    def _get_url(self, quality: StreamQuality) -> HttpUrl:
        """Get URL of the track to stream."""
        logger.debug(f"Getting track url with quality {quality}…")
        return HttpUrl(self.deezer.get_track_url(self.token, quality.value))

    def _generate_blowfish_key(self) -> bytes:
        """Generate the blowfish key for Deezer streams.

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
    def release_date(self) -> date:
        """Get track release date."""
        return self._get_track_info_attribute("release_date")

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
        with self.session.get(str(url), stream=True) as r:
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
    def serialize(self) -> TrackShort:
        """Serialize current track."""
        return TrackShort(
            id=self.track_id,
            title=self.title,
            album=self.album,
            artist=self.artist,
            release_date=self.release_date,
        )
