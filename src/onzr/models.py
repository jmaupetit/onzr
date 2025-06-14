"""Onzr: Pydantic models."""

from typing import List, Optional

from pydantic import BaseModel


class QueueState(BaseModel):
    """Queue state."""

    playing: int | None
    queued: int


class ServerState(BaseModel):
    """Onzr server state."""

    # Does not support VLC Enums
    player: str
    queue: QueueState


class PlayerControl(BaseModel):
    """Player controls."""

    action: str
    state: ServerState


class ServerMessage(BaseModel):
    """Generic server message."""

    message: str


class ArtistShort(BaseModel):
    """A small model to represent an artist."""

    id: str
    name: str


class AlbumShort(BaseModel):
    """A small model to represent an artist."""

    id: str
    name: str
    release_date: Optional[str] = None
    artist: Optional[ArtistShort] = None


class TrackShort(BaseModel):
    """A small model to represent an artist."""

    id: str
    title: str
    album: AlbumShort


class TrackInfo(BaseModel):
    """Used track data."""

    id: int
    token: str
    duration: int
    artist: str
    title: str
    album: str
    picture: str


Collection = List[ArtistShort] | List[AlbumShort] | List[TrackShort]


class QueuedTrack(BaseModel):
    """Queued track."""

    current: bool
    position: int
    track: TrackShort


class QueuedTracks(BaseModel):
    """Queued Tracks list."""

    playing: int | None
    tracks: List[QueuedTrack]
