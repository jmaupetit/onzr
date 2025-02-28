"""Onzr: deezer client."""

import functools
import hashlib
import logging
import tempfile
from enum import StrEnum
from pprint import pformat

import deezer
import httpx
import vlc
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


class Track:
    """A Deezer track."""

    def __init__(
        self,
        client: DeezerClient,
        track_id: str,
        player: vlc.MediaPlayer,
        quality: StreamQuality | None = None,
    ) -> None:
        """Instantiate a new track."""
        self.deezer = client
        self.track_id = track_id
        self.player = player
        self.vlc = self.player.get_instance()
        self.quality = quality or self.deezer.quality
        self.track_info: dict = self._get_track_info()
        self.url: str = self._get_url()
        self.key: bytes = self._generate_blowfish_key()
        self.is_playable : bool = False

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
    def token(self):
        """Get track token."""
        return self.track_info["TRACK_TOKEN"]

    def fetch(self):
        """Play track."""
        # 5 seconds for a 128kbs file
        buffer = 128000 * 5
        chunk_sep = 2048
        chunk_size = 3 * chunk_sep
        fetched = 0

        with httpx.stream("GET", self.url, follow_redirects=True) as r:
            r.raise_for_status()
            size = int(r.headers.get("Content-Length", 0))
            logger.debug(f"Track size: {size}")

            with tempfile.NamedTemporaryFile() as fp:
                logger.debug(f"Temporary file name: {fp.name}")
                self.player.set_media(self.vlc.media_new(fp.name))

                for chunk in r.iter_raw(chunk_size):
                    if len(chunk) > chunk_sep:
                        dchunk = self._decrypt(chunk[:chunk_sep]) + chunk[chunk_sep:]
                    else:
                        dchunk = chunk
                    fp.write(dchunk)
                    fetched += chunk_size

                    if fetched >= buffer and not self.is_playable:
                        logger.debug("Buffering ok")
                        self.is_playable = True
                        self.player.play()
                        self.player.pause()
