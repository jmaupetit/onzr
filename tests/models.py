"""Test models."""

from datetime import date
from typing import Annotated, Optional

from pydantic import BaseModel, PlainSerializer


class BaseDeezerGWResponse(BaseModel):
    """Deezer API Gateway response base Model."""

    error: dict = {}
    results: BaseModel


class DeezerSong(BaseModel):
    """Deezer API Song."""

    SNG_ID: Annotated[int, PlainSerializer(str)]
    TRACK_TOKEN: str
    DURATION: Annotated[int, PlainSerializer(str)]
    ART_NAME: str
    SNG_TITLE: str
    VERSION: Optional[str] = None
    ALB_TITLE: str
    ALB_PICTURE: str
    PHYSICAL_RELEASE_DATE: Annotated[date, PlainSerializer(str)]
    FILESIZE_MP3_128: Annotated[int, PlainSerializer(str)]
    FILESIZE_MP3_320: Annotated[int, PlainSerializer(str)]
    FILESIZE_FLAC: Annotated[int, PlainSerializer(str)]
    FALLBACK: "Optional[DeezerSong]" = None


class DeezerSongResponse(BaseDeezerGWResponse):
    """Deezer API Gateway Song info response."""

    results: DeezerSong
