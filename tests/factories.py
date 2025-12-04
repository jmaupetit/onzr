"""Test factories."""

from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import PositiveInt

from onzr.models.core import AlbumShort, TrackShort
from onzr.models.deezer import DeezerAlbum, DeezerSong, DeezerSongResponse, DeezerTrack


class DeezerSongFactory(ModelFactory[DeezerSong]):
    """DeezerSong factory."""

    @classmethod
    def FILESIZE_MP3_128(cls) -> PositiveInt:
        """Force FILESIZE_MP3_128 to be at least 100."""
        return cls.__random__.randint(100, 10000)


class DeezerAlbumFactory(ModelFactory[DeezerAlbum]):
    """DeezerAlbum factory."""


class DeezerTrackFactory(ModelFactory[DeezerTrack]):
    """DeezerTrack factory."""


class DeezerSongResponseFactory(ModelFactory[DeezerSongResponse]):
    """DeezerSongResponse factory."""


class TrackShortFactory(ModelFactory[TrackShort]):
    """TrackShort factory."""


class AlbumShortFactory(ModelFactory[AlbumShort]):
    """AlbumShort factory."""
