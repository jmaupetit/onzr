"""Onzr: deezer client."""

import functools
import hashlib
import logging
from enum import IntEnum, StrEnum
from io import BytesIO
from pprint import pformat
from threading import Thread
from time import sleep

import deezer
import httpx
from Cryptodome.Cipher import Blowfish

from .config import settings

logger = logging.getLogger(__name__)


class StreamQuality(StrEnum):
    """Track stream quality."""

    MP3_128 = "MP3_128"
    MP3_320 = "MP3_320"
    FLAC = "FLAC"


class DeezerClient(deezer.Deezer):
    """A wrapper for the Deezer API client."""

    def __init__(
        self, arl: str | None = None, quality: StreamQuality | None = None
    ) -> None:
        """Instantiate the Deezer API client."""
        super().__init__()

        self.arl = arl or settings.arl
        self.quality = quality or settings.quality
        self._login()

    def _login(self):
        """Login to deezer API."""
        logger.info("Login in to deezer using defined ARL…")
        self.login_via_arl(self.arl)


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
        self.http_client = httpx.Client()
        self.quality = quality or self.deezer.quality
        self.track_info: dict = self._get_track_info()
        self.url: str = self._get_url()
        self.key: bytes = self._generate_blowfish_key()
        self.status: TrackStatus = TrackStatus.IDLE
        self.content: bytearray = bytearray(self.filesize)
        self._content_mv: memoryview = memoryview(self.content)
        self.fetched: int = 0
        self.streamed: int = 0
        self.bitrate = self.filesize / self.duration
        self.buffer_size: int = int(self.bitrate * buffer)

    def _get_track_info(self) -> dict:
        """Get track info."""
        track_info = self.deezer.gw.get_track(self.track_id)
        logger.debug("Track info: %s", pformat(track_info))
        return track_info

    def _get_url(self) -> str:
        """Get URL of the track to stream."""
        logger.info(f"Getting track url with quality {self.quality}…")
        url = self.deezer.get_track_url(self.token, self.quality.value)
        logger.debug(f"Track url: {url}")
        return url

    def _generate_blowfish_key(self) -> bytes:
        """Generate the blowfish key for Deezer downloads.

        Taken from: https://github.com/nathom/streamrip/
        """
        md5_hash = hashlib.md5(self.track_id.encode()).hexdigest()
        # good luck :)
        return "".join(
            chr(functools.reduce(lambda x, y: x ^ y, map(ord, t)))
            for t in zip(md5_hash[:16], md5_hash[16:], settings.DEEZER_BLOWFISH_SECRET)
        ).encode()

    def _decrypt(self, chunk):
        """Decrypt blowfish encrypted chunk."""
        return Blowfish.new(
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

    def fetch(self):
        """Fetch track in-memory.

        buffer_size (int): the buffer size (defaults to 5 seconds for a 128kbs file)
        """
        logger.debug(f"Start fetching track with {self.buffer_size=}")
        chunk_sep = 2048
        chunk_size = 3 * chunk_sep
        self.fetched = 0
        self.status = TrackStatus.IDLE

        with self.http_client.stream("GET", self.url, follow_redirects=True) as r:
            r.raise_for_status()
            filesize = int(r.headers.get("Content-Length", 0))
            logger.debug(f"Track size: {filesize} ({self.filesize})")
            self.status = TrackStatus.FETCHING

            for chunk in r.iter_raw(chunk_size):
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
            # We have buffer issues
            while self.fetched - self.streamed < self.buffer_size:
                if not slow_connection:
                    logger.warning(
                        "Slow connection, filling the buffer "
                        f"{self.fetched - self.streamed} < {self.buffer_size}"
                    )
                slow_connection = True
                sleep(0.01)
            slow_connection = False

            socket.sendto(self._content_mv[start : start + chunk_size], multicast_group)
            self.streamed += chunk_size
            sleep(wait)
