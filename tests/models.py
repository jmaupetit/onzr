"""Test models."""

from pydantic import BaseModel


class BaseDeezerGWResponse(BaseModel):
    """Deezer API Gateway response base Model."""

    error: dict = {}
    results: BaseModel


class DeezerSong(BaseModel):
    """Deezer API Song."""

    SNG_ID: int
    TRACK_TOKEN: str
    DURATION: int
    ART_NAME: str
    SNG_TITLE: str
    VERSION: str | None = None
    ALB_TITLE: str
    ALB_PICTURE: str
    FILESIZE_MP3_128: int
    FILESIZE_MP3_320: int
    FILESIZE_FLAC: int


class DeezerSongResponse(BaseDeezerGWResponse):
    """Deezer API Gateway Song info response."""

    results: DeezerSong
