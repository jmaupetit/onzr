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
    ALB_TITLE: str
    ALB_PICTURE: str


class DeezerSongResponse(BaseDeezerGWResponse):
    """Deezer API Gateway Song info response."""

    results: DeezerSong
