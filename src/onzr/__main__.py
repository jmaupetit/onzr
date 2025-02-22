"""Onzr."""

import functools
import hashlib
import logging
import tempfile
import time
from enum import StrEnum
from pprint import pformat

import deezer
import httpx
import vlc
from Cryptodome.Cipher import Blowfish

from .config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class StreamQuality(StrEnum):
    """Track stream quality."""

    MP3_128 = "MP3_128"
    MP3_320 = "MP3_320"
    FLAC = "FLAC"


def get_track_url(
    client: deezer.Deezer, track_id: str, quality: StreamQuality = StreamQuality.MP3_128
):
    """Get URL of the track to stream."""
    logger.info("Getting track url for track_id {track_id} with quality {quality} …")
    track_info = client.gw.get_track(track_id)
    logger.debug("Track info: %s", pformat(track_info))

    token = track_info["TRACK_TOKEN"]
    url = client.get_track_url(token, quality.value)
    logger.debug(f"Track url: {url}")

    return url


def generate_blowfish_key(track_id: str) -> bytes:
    """Generate the blowfish key for Deezer downloads.

    Taken from: https://github.com/nathom/streamrip/
    """
    md5_hash = hashlib.md5(track_id.encode()).hexdigest()
    # good luck :)
    return "".join(
        chr(functools.reduce(lambda x, y: x ^ y, map(ord, t)))
        for t in zip(md5_hash[:16], md5_hash[16:], settings.DEEZER_BLOWFISH_SECRET)
    ).encode()


def decrypt(key, chunk):
    """Decrypt blowfish encrypted chunk."""
    return Blowfish.new(
        key,
        Blowfish.MODE_CBC,
        b"\x00\x01\x02\x03\x04\x05\x06\x07",
    ).decrypt(chunk)


def play_track(track_id: str, url: str):
    """Play track id given its URL."""
    # 5 seconds for a 128kbs file
    buffer = 128000 * 5
    chunk_sep = 2048
    chunk_size = 3 * chunk_sep
    key = generate_blowfish_key(track_id)
    fetched = 0
    is_playing = False

    with httpx.stream("GET", url, follow_redirects=True) as r:
        r.raise_for_status()
        size = int(r.headers.get("Content-Length", 0))
        logger.debug(f"Track size: {size}")

        with tempfile.NamedTemporaryFile() as fp:
            logger.debug(f"Temporary file name: {fp.name}")
            media = instance.media_new(fp.name)
            player.set_media(media)

            for chunk in r.iter_raw(chunk_size):
                if len(chunk) > chunk_sep:
                    dchunk = decrypt(key, chunk[:chunk_sep]) + chunk[chunk_sep:]
                else:
                    dchunk = chunk
                fp.write(dchunk)
                fetched += chunk_size

                if fetched >= buffer and not is_playing:
                    logger.debug("Buffer ok. Will start playing.")
                    player.play()
                    is_playing = True


if __name__ == "__main__":
    # Deezer API client
    logger.info("Login in to deezer…")
    client = deezer.Deezer()
    client.login_via_arl(settings.ARL)

    # VLC player
    instance = vlc.Instance()
    player = instance.media_player_new()
    # FIXME
    vlc.libvlc_video_set_key_input(player, on=True)

    track_id = "2107136627"
    quality = StreamQuality.MP3_128
    url = get_track_url(client, track_id, quality=quality)
    play_track(track_id, url)

    # Infinite loop while running the CLI
    while True:
        time.sleep(10)
