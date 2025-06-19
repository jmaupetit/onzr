"""Onzr: core module."""

import logging
import random
from typing import List

from vlc import MediaList

from onzr.config import get_settings

from .deezer import Track
from .models import QueuedTrack, QueuedTracks, QueueState

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
    def current(self) -> Track | None:
        """Get the current track."""
        if self.playing is None:
            return None
        return self.tracks[self.playing]

    @property
    def next(self) -> Track | None:
        """Get the next track (if any)."""
        rank = self.playing or 0 + 1
        if rank >= len(self):
            return None
        return self.tracks[rank]

    @property
    def state(self) -> QueueState:
        """Get queue state."""
        return QueueState(playing=self.playing, queued=len(self))

    def index_for_id(self, track_id) -> int:
        """Get track queue index given its id.

        If the same track is queued mutiple times only the first occurence index
        is returned.
        """
        return [t.track_id for t in self.tracks].index(track_id)

    def add(self, tracks: List[Track]):
        """Add one or more tracks to queue."""
        self.tracks.extend(tracks)

        # Add track streaming url to the playlist
        vlc_instance = self.playlist.get_instance()
        settings = get_settings()
        for t in tracks:
            media = vlc_instance.media_new(
                settings.TRACK_STREAM_URL.format(track_id=t.track_id)
            )
            self.playlist.add_media(media)

    def clear(self):
        """Empty queue."""
        self.playing = None
        self.tracks = []
        # FIXME: its not released!
        self.playlist.release()

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
