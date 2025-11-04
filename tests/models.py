"""Test models."""

from typing import Annotated

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
    VERSION: str | None = None
    ALB_TITLE: str
    ALB_PICTURE: str
    FILESIZE_MP3_128: Annotated[int, PlainSerializer(str)]
    FILESIZE_MP3_320: Annotated[int, PlainSerializer(str)]
    FILESIZE_FLAC: Annotated[int, PlainSerializer(str)]


class DeezerSongResponse(BaseDeezerGWResponse):
    """Deezer API Gateway Song info response."""

    results: DeezerSong
