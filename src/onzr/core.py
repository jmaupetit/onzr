"""Onzr: core module."""

import logging
import socket
import struct
from socket import SocketType

from .deezer import DeezerClient, StreamQuality, Track
from .player import Player

logger = logging.getLogger(__name__)


class Onzr:
    """Onzr core class."""

    def __init__(self) -> None:
        """Initialize all the things."""
        logger.debug("Instantiating Onzr…")

        self.deezer: DeezerClient = DeezerClient()
        self.socket: SocketType = self.configure_socket()
        self.player: Player = Player(self.socket)

    def configure_socket(self):
        """Open and configure the casting socket."""
        logger.debug("Setting socket…")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

        # Configure TTL
        ttl = struct.pack("b", 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        logger.debug(f"Socket: {sock}")
        return sock

    def play(self, track_id: str, quality: StreamQuality = StreamQuality.MP3_320):
        """Little helper to play a track."""
        self.player.play(Track(self.deezer, track_id, quality))
