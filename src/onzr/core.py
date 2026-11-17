"""Onzr: core module."""

import asyncio
import logging
import random
from functools import cached_property
from time import monotonic
from typing import List

from vlc import Instance, MediaList, MediaListPlayer, State

from onzr.config import get_settings

from .deezer import DeezerClient, Track
from .models.core import QueuedTrack, QueuedTracks, QueueState, ServerState

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
    """Onzr main class that communicates with all components.

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
            connection_pool_maxsize=self.settings.CONNECTION_POOL_MAXSIZE,
            always_fetch_release_date=self.settings.ALWAYS_FETCH_RELEASE_DATE,
        )

        # Player
        vlc_instance: Instance = Instance()
        self.player: MediaListPlayer = vlc_instance.media_list_player_new()

        # Queue
        self.queue: Queue = Queue(player=self.player)

    def state(self) -> ServerState:
        """Get Onzr state."""
        return ServerState(player=str(self.player.get_state()), queue=self.queue.state)

    async def settled_state(self) -> ServerState:
        """Get Onzr state once the player left transient states.

        After a player control action, VLC needs some time to update its state. When
        playing, it also needs to fetch the track stream from this very server (which
        updates the queue playing index), so we must not block the event loop while
        waiting.
        """
        await asyncio.sleep(self.settings.STATE_DELAY)
        deadline = monotonic() + self.settings.STATE_TIMEOUT
        while (
            self.player.get_state() in (State.Opening, State.Buffering)
            and monotonic() < deadline
        ):
            await asyncio.sleep(self.settings.STATE_POLL_INTERVAL)
        return self.state()
