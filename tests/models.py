"""Test models."""

from datetime import date
from typing import Annotated, Optional

from annotated_types import Ge, Gt
from pydantic import BaseModel, PlainSerializer, PositiveInt


class BaseDeezerGWResponse(BaseModel):
    """Deezer API Gateway response base Model."""

    error: dict = {}
    results: BaseModel


class DeezerSong(BaseModel):
    """Deezer API Song."""

    SNG_ID: Annotated[int, Gt(0), PlainSerializer(str)]
    TRACK_TOKEN: str
    DURATION: Annotated[int, Gt(0), PlainSerializer(str)]
    ART_NAME: str
    SNG_TITLE: str
    VERSION: Optional[str] = None
    ALB_TITLE: str
    ALB_PICTURE: str
    PHYSICAL_RELEASE_DATE: Annotated[date, PlainSerializer(str)]
    FILESIZE_MP3_128: Annotated[int, Ge(0), PlainSerializer(str)]
    FILESIZE_MP3_320: Annotated[int, Ge(0), PlainSerializer(str)]
    FILESIZE_FLAC: Annotated[int, Ge(0), PlainSerializer(str)]
    FALLBACK: "Optional[DeezerSong]" = None


class DeezerSongResponse(BaseDeezerGWResponse):
    """Deezer API Gateway Song info response."""

    results: DeezerSong


class DeezerAlbum(BaseModel):
    """Deezer API album."""

    title: str


class DeezerArtist(BaseModel):
    """Deezer API artist."""

    name: str


class DeezerTrack(BaseModel):
    """Deezer API track."""

    id: PositiveInt
    title: str
    album: DeezerAlbum
    artist: DeezerArtist
    release_date: date
