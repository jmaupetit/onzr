"""Onzr: core module."""

import logging
import random
import socket
import struct
from socket import SocketType
from typing import List

from .deezer import DeezerClient, StreamQuality, Track
from .player import Player

logger = logging.getLogger(__name__)


class Queue:
    """Onzr playing queue."""

    def __init__(self) -> None:
        """Instantiate the tracks queue."""
        self.current: Track | None = None
        self.tracks: List[Track] = []

    def __len__(self):
        """Get queue length."""
        return len(self.tracks)

    @property
    def is_empty(self):
        """Check if tracks are queued."""
        return len(self) == 0 and self.current is None

    def add(self, track: Track | None = None, tracks: List[Track] | None = None):
        """Add one or more tracks to queue."""
        if track is None and tracks is None:
            raise TypeError("Argument missing, you should either add a track or tracks")
        self.tracks.extend(tracks or [track])  # type: ignore[list-item]

    def shuffle(self):
        """Shuffle current track list."""
        random.shuffle(self.tracks)

    def next(self):
        """Set next track as the current."""
        del self.current
        if not len(self):
            self.current = None
            return
        self.current = self.tracks.pop(0)


class Onzr:
    """Onzr core class."""

    def __init__(self, fast: bool = False) -> None:
        """Initialize all the things.

        fast (bool): activate Deezer fast login
        """
        logger.debug("Instantiating Onzr…")

        self.deezer: DeezerClient = DeezerClient(fast=fast)
        self.socket: SocketType = self.configure_socket()
        self.player: Player = Player(self.socket)
        self._queue: Queue = Queue()

    def configure_socket(self):
        """Open and configure the casting socket."""
        logger.debug("Setting socket…")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

        # Configure TTL
        ttl = struct.pack("b", 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        logger.debug(f"Socket: {sock}")
        return sock

    def add(self, track_ids: List[str], quality: StreamQuality = StreamQuality.MP3_320):
        """Little helper to queue tracks."""
        logger.info("➕ Adding new tracks to queue…")
        tracks = [Track(self.deezer, track_id, quality) for track_id in track_ids]
        for track in tracks:
            logger.info(f"{track.full_title}")
        self._queue.add(tracks=tracks)
        logger.info(f"✅ {len(tracks)} tracks queued")

    def shuffle(self):
        """Shuffle tracks queue."""
        logger.info("🔀 Shuffling tracks queue…")
        self._queue.shuffle()
        for track in self._queue.tracks:
            logger.info(f"{track.full_title}")

    def play(self):
        """Little helper to start playing the queue."""
        # No active track, try to queue the next one in line
        if self._queue.current is None:
            self._queue.next()

        # There is no track left in queue
        if self._queue.is_empty:
            return

        # Play current track
        self.player.play(self._queue.current)
        self._queue.next()

        return self.play()
