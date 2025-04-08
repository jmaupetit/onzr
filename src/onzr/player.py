"""Onzr: player."""

import logging
from socket import SocketType

import vlc
from vlc import MediaPlayer

from .config import settings
from .deezer import Track

logger = logging.getLogger(__name__)


class Player:
    """Onzr player."""

    def __init__(self, socket: SocketType, local: bool = True) -> None:
        """Instantiate the player."""
        logger.debug(f"Instantiating Player using socket: {socket} ({local=})")
        self.socket: SocketType = socket
        self.track: Track | None = None
        self.chunk_size: int = 1024 * 4
        self.vlc: MediaPlayer | None = None
        if local:
            self._start_udp_client(settings.MULTICAST_URL)

    def _start_udp_client(self, url: str):
        """Start local UDP client.

        Start a local UDP client that will listen to the UDP socket and play sound.
        """
        logger.debug(f"Starting local UDP client with: {url=}")
        self.vlc = vlc.MediaPlayer(url)
        self.vlc.play()

    def play(self, track: Track):
        """Play a track."""
        logger.info(f"▶️ {track.full_title}")
        self.track = track
        self.track.cast(self.socket, self.chunk_size)
