"""Onzr: Pydantic models."""

from enum import StrEnum
from typing import Annotated, List, Optional, TypeAlias

from pydantic import BaseModel, Field, PositiveInt
from pydantic_extra_types.color import Color


class OnzrTheme(BaseModel):
    """Onzr theme."""

    primary_color: Color
    secondary_color: Color
    tertiary_color: Color
    title_color: Color
    artist_color: Color
    album_color: Color
    alert_color: Color


class QueueState(BaseModel):
    """Queue state."""

    playing: int | None
    queued: int


class ServerState(BaseModel):
    """Onzr server state."""

    # Does not support VLC Enums
    player: str
    queue: QueueState


class StreamQuality(StrEnum):
    """Track stream quality."""

    MP3_128 = "MP3_128"
    MP3_320 = "MP3_320"
    FLAC = "FLAC"

    @property
    def media_type(self) -> str:
        """Get media type corresponding to selected quality."""
        if self == StreamQuality.FLAC:
            return "audio/flac"
        return "audio/mpeg"


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
    duration: PositiveInt
    formats: List[StreamQuality]


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

    def __len__(self):
        """Get tracks length."""
        return len(self.tracks)


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

    rank: Optional[Annotated[int, Field(strict=True, ge=0)]] = None
