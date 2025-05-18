"""Onzr: core module."""

import logging
import random
import socket
import struct
from enum import IntEnum
from socket import SocketType
from typing import List

from dynaconf import Dynaconf
from vlc import MediaList

from .config import get_settings
from .deezer import DeezerClient, StreamQuality, Track
from .exceptions import OnzrConfigurationError
from .player import Player

logger = logging.getLogger(__name__)


class Queue:
    """Onzr playing queue."""

    def __init__(self, playlist: MediaList) -> None:
        """Instantiate the tracks queue."""
        self.playing: int | None = None
        self.tracks: List[Track] = []
        self.playlist: MediaList = playlist

    def __len__(self):
        """Get queue length."""
        return len(self.tracks)

    def __getitem__(self, index: int) -> Track:
        """Get track from its queue index."""
        return self.tracks[index]

    @property
    def is_empty(self):
        """Check if tracks are queued."""
        return len(self) == 0

    @property
    def current(self):
        """Get the current track."""
        return self.tracks[self.playing]

    def index_for_id(self, track_id) -> int:
        """Get track queue index given its id.

        If the same track is queued mutiple times only the first occurence index
        is returned.
        """
        return [t.track_id for t in self.tracks].index(track_id)

    def add(self, track: Track | None = None, tracks: List[Track] | None = None):
        """Add one or more tracks to queue."""
        if track is None and tracks is None:
            raise TypeError("Argument missing, you should either add a track or tracks")

        tracks = tracks or [track]
        self.tracks.extend(tracks)  # type: ignore[list-item]

        # Add track streaming url to the playlist
        vlc_instance = self.playlist.get_instance()
        for t in tracks:
            media = vlc_instance.media_new(
                # FIXME: URL should be configurable
                f"http://localhost:9473/queue/{t.track_id}/stream"
            )
            self.playlist.add_media(media)

    def clear(self):
        """Empty queue."""
        self.playing = None
        self.tracks = []
        self.playlist.release()

    def shuffle(self):
        """Shuffle current track list."""
        random.shuffle(self.tracks)


class OnzrStatus(IntEnum):
    """Onzr player status."""

    IDLE = 1
    PLAYING = 2
    PAUSED = 3
    STOPPED = 4


class Onzr:
    """Onzr core class."""

    def __init__(self, fast: bool = False) -> None:
        """Initialize all the things.

        fast (bool): fast boot (not player) and fast login mode (for Deezer)
        """
        logger.debug("Instantiating Onzr…")
        self.settings: Dynaconf = get_settings()
        self._ensure_settings()

        self.deezer: DeezerClient = DeezerClient(
            arl=self.settings.arl,
            blowfish=self.settings.DEEZER_BLOWFISH_SECRET,
            multicast_group=self.settings.MULTICAST_GROUP,
            fast=fast,
        )

        # We just make API requests
        if fast:
            return

        self.socket: SocketType = self.configure_socket()
        self.player: Player = Player(
            self.socket, local=True, multicast_url=self.settings.MULTICAST_URL
        )
        self._queue: Queue = Queue()
        self.status: OnzrStatus = OnzrStatus.IDLE

    def _ensure_settings(self):
        """Ensure Onzr settings are valid."""
        # Settings or secret files does not exist
        try:
            self.settings.get("arl")
        except OSError as err:
            raise OnzrConfigurationError(
                "Onzr is not configured. You should run the 'onzr init' command first."
            ) from err

        # ARL is not set
        if self.settings.get("arl", None) is None:
            raise OnzrConfigurationError(
                "Onzr is not properly configured. You should set the ARL secret."
            )

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
        self.status = OnzrStatus.PLAYING
        self._queue.current.paused = False
        self.player.play(self._queue.current)
        self._queue.next()

        return self.play()

    def pause(self):
        """Pause current track playing."""
        logger.info("⏯ Toggling pause…")
        logger.debug(f"Onzr Status? {self.status.name}")
        if self._queue.current is None:
            return

        if self.status == OnzrStatus.PLAYING:
            self.status = OnzrStatus.PAUSED
            self._queue.current.paused = True
        elif self.status == OnzrStatus.PAUSED:
            self.status = OnzrStatus.PLAYING
            self._queue.current.paused = False
