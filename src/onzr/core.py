"""Onzr: core module."""

import logging
import random
from typing import List

from vlc import MediaList

from onzr.config import get_settings

from .deezer import Track

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
