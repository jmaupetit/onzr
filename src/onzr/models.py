"""Onzr: Pydantic models."""

from typing import Annotated, List, Optional, TypeAlias

from pydantic import BaseModel, Field


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

    id: int
    name: str


class AlbumShort(BaseModel):
    """A small model to represent an artist."""

    id: int
    title: str
    artist: Optional[str] = None
    release_date: Optional[str] = None

    def __hash__(self):
        """Make AlbumShort hashable."""
        return hash(self.id)


class TrackShort(BaseModel):
    """A small model to represent an artist."""

    id: int
    title: str
    album: str
    artist: str


class TrackInfo(BaseModel):
    """Used track data."""

    id: int
    title: str
    album: str
    artist: str
    picture: str
    token: str
    duration: int


Collection: TypeAlias = List[ArtistShort] | List[AlbumShort] | List[TrackShort]


class QueuedTrack(BaseModel):
    """Queued track."""

    current: bool
    position: int
    track: TrackShort


class QueuedTracks(BaseModel):
    """Queued Tracks list."""

    playing: int | None
    tracks: List[QueuedTrack]


class PlayerState(BaseModel):
    """Detailled player state."""

    state: str
    length: int = 0
    time: int = 0
    position: float = 0.0


class PlayingState(BaseModel):
    """Playing player state."""

    player: PlayerState
    track: Optional[TrackShort] = None


class PlayQueryParams(BaseModel):
    """Play endpoint parameters."""

    rank: Optional[Annotated[int, Field(strict=True, gt=0)]] = None
