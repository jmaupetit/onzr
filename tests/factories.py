"""Test factories."""

from polyfactory.factories.pydantic_factory import ModelFactory

from .models import DeezerSong, DeezerSongResponse


class DeezerSongFactory(ModelFactory[DeezerSong]):
    """DeezerSong factory."""


class DeezerSongResponseFactory(ModelFactory[DeezerSongResponse]):
    """DeezerSongResponse factory."""
