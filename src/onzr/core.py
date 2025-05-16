"""Onzr: core module."""

import logging
import random
from functools import cached_property
from time import sleep
from typing import List

from vlc import Instance, MediaList, MediaListPlayer

from onzr.config import get_settings

from .deezer import DeezerClient, Track
from .models import QueuedTrack, QueuedTracks, QueueState, ServerState

logger = logging.getLogger(__name__)


class Queue:
    """Onzr playing queue."""

    def __init__(self, player: MediaListPlayer) -> None:
        """Instantiate the tracks queue."""
        self.playing: int | None = None
        self.tracks: List[Track] = []
        self.player: MediaListPlayer = player
        self.playlist: MediaList = self._activate_new_playlist(self.player)

    def __len__(self):
        """Get queue length."""
        return len(self.tracks)

    def __getitem__(self, index: int) -> Track:
        """Get track from its queue index."""
        return self.tracks[index]

    @cached_property
    def vlc_instance(self):
        """Get VLC instance."""
        return self.player.get_instance()

    @property
    def is_empty(self):
        """Check if tracks are queued."""
        return len(self) == 0

    @property
    def current(self) -> Track | None:
        """Get the current track."""
        if self.playing is None:
            return None
        return self.tracks[self.playing]

    @property
    def state(self) -> QueueState:
        """Get queue state."""
        return QueueState(playing=self.playing, queued=len(self))

    def _activate_new_playlist(self, player: MediaListPlayer) -> MediaList:
        """Create a new playlist and activate the media player with it."""
        playlist = self.vlc_instance.media_list_new()
        player.set_media_list(playlist)
        return playlist

    def add(self, tracks: List[Track]):
        """Add one or more tracks to queue."""
        start = len(self)
        self.tracks.extend(tracks)

        # Add track streaming url to the playlist
        vlc_instance = self.playlist.get_instance()
        settings = get_settings()
        for rank in range(start, start + len(tracks), 1):
            media = vlc_instance.media_new(settings.TRACK_STREAM_URL.format(rank=rank))
            self.playlist.add_media(media)

    def clear(self):
        """Empty queue."""
        self.playing = None
        self.tracks = []

        # Player-related part
        if self.playlist:
            self.playlist.release()
        self.playlist = self._activate_new_playlist(self.player)

    def shuffle(self):
        """Shuffle current track list."""
        random.shuffle(self.tracks)

    def serialize(self) -> QueuedTracks:
        """Serialize queue."""
        return QueuedTracks(
            playing=self.playing,
            tracks=[
                QueuedTrack(current=self.playing == p, position=p, track=t.serialize())
                for p, t in enumerate(self.tracks)
            ],
        )


class Onzr:
    """Onzr main class that communicates with every components.

    - deezer: Deezer API client
    - player: VLC player
    - queue: Queue instance
    """

    def __init__(self) -> None:
        """Instantiate components."""
        self.settings = get_settings()

        # Deezer API client
        self.deezer: DeezerClient = DeezerClient(
            arl=self.settings.ARL,
            blowfish=self.settings.DEEZER_BLOWFISH_SECRET,
            fast=False,
        )

        # Player
        vlc_instance: Instance = Instance()
        self.player: MediaListPlayer = vlc_instance.media_list_player_new()

        # Queue
        self.queue: Queue = Queue(player=self.player)

    def state(self) -> ServerState:
        """Get Onzr state."""
        # Wait a bit before returning the server/player state, since after performing
        # a control action on the player, its state may need some time to get updated.
        sleep(self.settings.STATE_DELAY)

        return ServerState(player=str(self.player.get_state()), queue=self.queue.state)
