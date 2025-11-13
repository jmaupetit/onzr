"""Test factories."""

from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import PositiveInt

from .models import DeezerSong, DeezerSongResponse, DeezerTrack


class DeezerSongFactory(ModelFactory[DeezerSong]):
    """DeezerSong factory."""

    @classmethod
    def FILESIZE_MP3_128(cls) -> PositiveInt:
        """Force FILESIZE_MP3_128 to be at least 100."""
        return cls.__random__.randint(100, 10000)


class DeezerTrackFactory(ModelFactory[DeezerTrack]):
    """DeezerTrack factory."""


class DeezerSongResponseFactory(ModelFactory[DeezerSongResponse]):
    """DeezerSongResponse factory."""
